# -*- coding: utf-8 -*-
"""
Sistema Integral de Gesti n de Clientes, Servicios y
Reservas
Curso: Programacion (213023) - Fase 4
Grupo: 213023_359
Fecha: Noviembre 2026
"""
import logging
import math
import re
import unicodedata
import sys
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import overload, Any
import tkinter as tk
from tkinter import ttk, messagebox

# ============================================================================
# Módulo integrado: excepciones/errores.py
# ============================================================================
"""Excepciones de dominio de Software FJ."""

class SoftwareFJError(Exception):
    """Excepción base del sistema."""

class ClienteInvalidoError(SoftwareFJError):
    """Datos de cliente inválidos."""

class ServicioInvalidoError(SoftwareFJError):
    """Datos o parámetros de servicio inválidos."""

class ReservaInvalidaError(SoftwareFJError):
    """Reserva inválida o transición de estado no permitida."""

class DisponibilidadError(SoftwareFJError):
    """Recurso o capacidad no disponible."""

class ElementoNoEncontradoError(SoftwareFJError):
    """No se encontró un elemento solicitado."""

class DuplicadoError(SoftwareFJError):
    """Identificador duplicado."""

class CalculoInvalidoError(SoftwareFJError):
    """No se pudo realizar un cálculo válido."""

# ============================================================================
# Módulo integrado: modelos/entidad_base.py
# ============================================================================
"""Entidad abstracta común del sistema."""

class EntidadBase(ABC):
    def __init__(self, identificador: str):
        if not isinstance(identificador, str) or not identificador.strip():
            raise ValueError("El identificador no puede estar vacío.")
        self._identificador = identificador.strip()

    @property
    def identificador(self) -> str:
        return self._identificador

    @abstractmethod
    def obtener_detalles(self) -> dict:
        """Devuelve los datos principales de la entidad."""

# ============================================================================
# Módulo integrado: modelos/cliente.py
# ============================================================================
"""Modelo de cliente con encapsulación y validaciones."""

class Cliente(EntidadBase):
    def __init__(self, identificador: str, nombre: str, correo: str, telefono: str):
        try:
            super().__init__(identificador)
        except (ValueError, TypeError) as exc:
            raise ClienteInvalidoError("El identificador del cliente es obligatorio.") from exc
        self.nombre = nombre
        self.correo = correo
        self.telefono = telefono

    @property
    def nombre(self):
        return self._nombre

    @nombre.setter
    def nombre(self, valor):
        if not isinstance(valor, str) or not valor.strip():
            raise ClienteInvalidoError("El nombre no puede estar vacío.")
        if len(valor.strip()) < 2:
            raise ClienteInvalidoError("El nombre debe contener al menos 2 caracteres.")
        self._nombre = valor.strip()

    @property
    def correo(self):
        return self._correo

    @correo.setter
    def correo(self, valor):
        patron = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
        if not isinstance(valor, str) or not re.fullmatch(patron, valor.strip()):
            raise ClienteInvalidoError(f"El correo '{valor}' no tiene un formato válido.")
        self._correo = valor.strip().lower()

    @property
    def telefono(self):
        return self._telefono

    @telefono.setter
    def telefono(self, valor):
        if not isinstance(valor, str):
            valor = str(valor) if isinstance(valor, int) else ""
        limpio = re.sub(r"[\s()+-]", "", valor)
        if not limpio.isdigit() or not 7 <= len(limpio) <= 15:
            raise ClienteInvalidoError("El teléfono debe contener entre 7 y 15 dígitos.")
        self._telefono = limpio

    def obtener_detalles(self):
        return {
            "tipo": "Cliente", "id": self.identificador,
            "nombre": self.nombre, "correo": self.correo,
            "telefono": self.telefono
        }

    def __str__(self):
        return f"{self.identificador} - {self.nombre} ({self.correo})"


# ============================================================================
# Módulo integrado: modelos/servicio.py
# ============================================================================
"""Clase abstracta Servicio y reglas comunes de cálculo."""

class Servicio(EntidadBase, ABC):
    """Contrato común de todos los servicios ofrecidos por Software FJ."""

    IMPUESTO = 0.19

    def __init__(self, identificador: str, nombre_servicio: str, costo_base: float):
        try:
            super().__init__(identificador)
        except (ValueError, TypeError) as exc:
            raise ServicioInvalidoError(
                "El identificador del servicio es obligatorio."
            ) from exc
        if not isinstance(nombre_servicio, str) or not nombre_servicio.strip():
            raise ServicioInvalidoError("El nombre del servicio es obligatorio.")
        self._nombre_servicio = nombre_servicio.strip()
        self.costo_base = costo_base

    @property
    def nombre_servicio(self) -> str:
        return self._nombre_servicio

    @property
    def costo_base(self) -> float:
        return self._costo_base

    @costo_base.setter
    def costo_base(self, valor: float) -> None:
        if isinstance(valor, bool) or not isinstance(valor, (int, float)):
            raise ServicioInvalidoError("El costo base debe ser numérico.")
        if not math.isfinite(valor) or valor < 0:
            raise ServicioInvalidoError("El costo base debe ser finito y no negativo.")
        self._costo_base = float(valor)

    @abstractmethod
    def validar_parametros(self, **kwargs) -> bool:
        """Valida los parámetros específicos del servicio."""
        raise NotImplementedError

    @abstractmethod
    def describir_servicio(self) -> str:
        """Devuelve una descripción legible del servicio."""
        raise NotImplementedError

    @abstractmethod
    def _factor_cantidad(self, **kwargs) -> float:
        """Calcula el factor de unidades o nivel específico del servicio."""
        raise NotImplementedError

    # Python no implementa sobrecarga tradicional por firma en tiempo de ejecución.
    # @overload documenta las formas válidas para analizadores de tipos; la
    # implementación real acepta argumentos opcionales y parámetros específicos.
    @overload
    def calcular_costo(self, duracion: float, **kwargs: Any) -> float: ...

    @overload
    def calcular_costo(
        self, duracion: float, descuento: float, **kwargs: Any
    ) -> float: ...

    @overload
    def calcular_costo(
        self, duracion: float, descuento: float, aplicar_impuesto: bool,
        **kwargs: Any
    ) -> float: ...

    def calcular_costo(
        self,
        duracion: float,
        descuento: float = 0.0,
        aplicar_impuesto: bool = True,
        **kwargs
    ) -> float:
        """Calcula el total con descuento opcional e impuesto opcional.

        Variantes admitidas:
        - calcular_costo(duracion)
        - calcular_costo(duracion, descuento)
        - calcular_costo(duracion, descuento, aplicar_impuesto)
        También admite parámetros específicos del servicio mediante kwargs.
        """
        if isinstance(duracion, bool) or not isinstance(duracion, (int, float)):
            raise CalculoInvalidoError("La duración debe ser numérica.")
        if not math.isfinite(duracion) or duracion <= 0:
            raise CalculoInvalidoError("La duración debe ser finita y mayor que cero.")
        if isinstance(descuento, bool) or not isinstance(descuento, (int, float)):
            raise CalculoInvalidoError("El descuento debe ser numérico.")
        if not math.isfinite(descuento) or descuento < 0:
            raise CalculoInvalidoError("El descuento debe ser finito y no negativo.")
        if not isinstance(aplicar_impuesto, bool):
            raise CalculoInvalidoError("aplicar_impuesto debe ser verdadero o falso.")

        # Cada regla de cantidad valida los parámetros que necesita; Reserva
        # también llama explícitamente a validar_parametros antes de confirmar.
        factor = self._factor_cantidad(**kwargs)
        if isinstance(factor, bool) or not isinstance(factor, (int, float)):
            raise CalculoInvalidoError("El factor de cantidad debe ser numérico.")
        if not math.isfinite(factor) or factor <= 0:
            raise CalculoInvalidoError("El factor de cantidad debe ser finito y positivo.")

        subtotal_bruto = self.costo_base * float(duracion) * float(factor)
        if not math.isfinite(subtotal_bruto) or subtotal_bruto < 0:
            raise CalculoInvalidoError("El subtotal calculado no es válido.")
        if descuento > subtotal_bruto:
            raise CalculoInvalidoError("El descuento no puede superar el subtotal.")

        subtotal = subtotal_bruto - float(descuento)
        total = subtotal * (1 + self.IMPUESTO) if aplicar_impuesto else subtotal
        if not math.isfinite(total) or total < 0:
            raise CalculoInvalidoError("El cálculo produjo un resultado inconsistente.")
        return round(total, 2)

    def calcular_costo_con_descuento(self, duracion: float, descuento: float, **kwargs) -> float:
        """Variante explícita: calcula el costo aplicando descuento e impuesto."""
        return self.calcular_costo(
            duracion, descuento=descuento, aplicar_impuesto=True, **kwargs
        )

    def calcular_costo_sin_impuesto(self, duracion: float, descuento: float = 0.0, **kwargs) -> float:
        """Variante explícita: calcula el costo sin aplicar el impuesto."""
        return self.calcular_costo(
            duracion, descuento=descuento, aplicar_impuesto=False, **kwargs
        )

    def calcular_costo_con_impuesto(self, duracion: float, descuento: float = 0.0, **kwargs) -> float:
        """Variante explícita: calcula el costo aplicando el impuesto."""
        return self.calcular_costo(
            duracion, descuento=descuento, aplicar_impuesto=True, **kwargs
        )

    def __str__(self) -> str:
        return self.describir_servicio()

    def obtener_detalles(self) -> dict:
        return {
            "tipo": self.nombre_servicio,
            "id": self.identificador,
            "costo_base": self.costo_base,
        }
# ============================================================================
# Jhon Alexander Cuaran 
# Módulo integrado: modelos/reserva_sala.py
# ============================================================================

class ReservaSala(Servicio):
    def __init__(self, identificador: str, costo_base: float, capacidad: int):
        super().__init__(identificador, "Reserva de sala", costo_base)
        if isinstance(capacidad, bool) or not isinstance(capacidad, int) or capacidad <= 0:
            raise ServicioInvalidoError("La capacidad de la sala debe ser un entero positivo.")
        self._capacidad = capacidad

    @property
    def capacidad(self):
        return self._capacidad

    def validar_parametros(self, **kwargs):
        personas = kwargs.get("personas")
        if isinstance(personas, bool) or not isinstance(personas, int) or personas <= 0:
            raise ServicioInvalidoError("Debe indicar un número entero positivo de personas.")
        if personas > self.capacidad:
            raise DisponibilidadError(
                f"La sala admite {self.capacidad} personas y se solicitaron {personas}."
            )
        return True

    def _factor_cantidad(self, **kwargs):
        return 1.0

    def calcular_costo(
        self, duracion: float, descuento: float = 0.0,
        aplicar_impuesto: bool = True, **kwargs
    ) -> float:
        """Sobrescribe el cálculo para validar las personas de la sala."""
        self.validar_parametros(**kwargs)
        return super().calcular_costo(
            duracion, descuento, aplicar_impuesto, **kwargs
        )

    def describir_servicio(self):
        return f"Sala {self.identificador}: capacidad máxima de {self.capacidad} personas."

    def obtener_detalles(self) -> dict:
        """Devuelve los datos del servicio de reserva de sala."""
        return {
            "tipo": "ReservaSala",
            "id": self.identificador,
            "nombre": self.nombre_servicio,
            "costo_base": self.costo_base,
            "capacidad": self.capacidad,
        }
# ============================================================================
# Módulo integrado: modelos/alquiler_equipo.py
# ============================================================================

class AlquilerEquipo(Servicio):
    def __init__(self, identificador: str, costo_base: float, tipo_equipo: str = "Equipo general"):
        super().__init__(identificador, "Alquiler de equipo", costo_base)
        if not isinstance(tipo_equipo, str) or not tipo_equipo.strip():
            tipo_equipo = "Equipo general"
        self._tipo_equipo = tipo_equipo.strip()

    @property
    def tipo_equipo(self):
        return self._tipo_equipo

    def validar_parametros(self, **kwargs):
        unidades = kwargs.get("unidades")
        if isinstance(unidades, bool) or not isinstance(unidades, int) or unidades <= 0:
            raise ServicioInvalidoError("Las unidades deben ser un entero positivo.")
        return True

    def _factor_cantidad(self, **kwargs):
        unidades = kwargs.get("unidades")
        self.validar_parametros(unidades=unidades)
        return float(unidades)

    def calcular_costo(
        self, duracion: float, descuento: float = 0.0,
        aplicar_impuesto: bool = True, **kwargs
    ) -> float:
        """Sobrescribe el cálculo para validar las unidades de equipo."""
        self.validar_parametros(**kwargs)
        return super().calcular_costo(
            duracion, descuento, aplicar_impuesto, **kwargs
        )

    def describir_servicio(self):
        return f"{self.tipo_equipo} (ID: {self.identificador}); tarifa por unidad y día."

    def obtener_detalles(self) -> dict:
        """Devuelve los datos del servicio de alquiler de equipo."""
        return {
            "tipo": "AlquilerEquipo",
            "id": self.identificador,
            "nombre": self.nombre_servicio,
            "costo_base": self.costo_base,
            "tipo_equipo": self.tipo_equipo,
        }
