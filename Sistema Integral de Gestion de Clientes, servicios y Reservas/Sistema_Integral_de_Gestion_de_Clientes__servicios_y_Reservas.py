# -*- coding: utf-8 -*-
"""
Sistema Integral de Gesti�n de Clientes, Servicios y
Reservas
Curso: Programacion (213023) - Fase 4
Grupo: 213023_359
Fecha: Noviembre 2026
"""
# Módulos estándar para registrar eventos, abrir archivos y trabajar con rutas.
import logging
import os
import subprocess
# Herramientas para cálculos, validación de texto y normalización de acentos.
import math
import re
import unicodedata
import sys
# Herramientas de programación orientada a objetos y anotaciones de tipos.
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import overload, Any
# Componentes para construir la interfaz gráfica de escritorio.
import tkinter as tk
from tkinter import ttk, messagebox

# ============================================================================
# Módulo integrado: excepciones/errores.py
# ============================================================================
"""Excepciones de dominio de Software FJ."""

class SoftwareFJError(Exception):
    """Excepción base del sistema; registra automáticamente errores de dominio."""

    def __init__(self, mensaje="Se produjo un error en Software FJ"):
        'Inicializa el objeto y valida o guarda sus datos iniciales.'
        super().__init__(mensaje)
        # La configuración se inicializa en los puntos de entrada de la aplicación.
        # Si ya está configurada, todo error de dominio queda registrado aquí,
        # incluso cuando la excepción se origina fuera de la interfaz o simulación.
        logging.error("%s: %s", self.__class__.__name__, mensaje)

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
    'Clase abstracta base de las entidades del sistema. Valida el identificador y exige implementar obtener_detalles().'
    def __init__(self, identificador: str):
        'Inicializa el objeto y valida o guarda sus datos iniciales.'
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
    'Representa un cliente y encapsula sus datos con propiedades que validan nombre, correo y teléfono.'
    def __init__(self, identificador: str, nombre: str, correo: str, telefono: str):
        'Inicializa el objeto y valida o guarda sus datos iniciales.'
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
        'Devuelve los datos principales del objeto en forma de diccionario.'
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
        'Inicializa el objeto y valida o guarda sus datos iniciales.'
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

        # El subtotal bruto combina tarifa base, duración y factor propio del servicio.
        subtotal_bruto = self.costo_base * float(duracion) * float(factor)
        if not math.isfinite(subtotal_bruto) or subtotal_bruto < 0:
            raise CalculoInvalidoError("El subtotal calculado no es válido.")
        if descuento > subtotal_bruto:
            raise CalculoInvalidoError("El descuento no puede superar el subtotal.")

        # El descuento se resta antes de calcular el impuesto.
        subtotal = subtotal_bruto - float(descuento)
        # El impuesto se aplica únicamente si aplicar_impuesto es True.
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
        'Devuelve los datos principales del objeto en forma de diccionario.'
        return {
            "tipo": self.nombre_servicio,
            "id": self.identificador,
            "costo_base": self.costo_base,
        }

# ============================================================================
# Módulo integrado: modelos/reserva_sala.py
# ============================================================================

class ReservaSala(Servicio):
    'Servicio especializado de reserva de salas; valida la cantidad de personas y la capacidad máxima.'
    def __init__(self, identificador: str, costo_base: float, capacidad: int):
        'Inicializa el objeto y valida o guarda sus datos iniciales.'
        super().__init__(identificador, "Reserva de sala", costo_base)
        if isinstance(capacidad, bool) or not isinstance(capacidad, int) or capacidad <= 0:
            raise ServicioInvalidoError("La capacidad de la sala debe ser un entero positivo.")
        self._capacidad = capacidad

    @property
    def capacidad(self):
        return self._capacidad

    def validar_parametros(self, **kwargs):
        'Valida los parámetros específicos que requiere este servicio.'
        personas = kwargs.get("personas")
        if isinstance(personas, bool) or not isinstance(personas, int) or personas <= 0:
            raise ServicioInvalidoError("Debe indicar un número entero positivo de personas.")
        if personas > self.capacidad:
            raise DisponibilidadError(
                f"La sala admite {self.capacidad} personas y se solicitaron {personas}."
            )
        return True

    def _factor_cantidad(self, **kwargs):
        'Calcula el multiplicador que depende de unidades o del nivel del servicio.'
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
        'Devuelve una descripción legible del servicio.'
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
    'Servicio especializado de alquiler de equipos; el precio depende de la duración y las unidades.'
    def __init__(self, identificador: str, costo_base: float, tipo_equipo: str):
        'Inicializa el objeto y valida o guarda sus datos iniciales.'
        super().__init__(identificador, "Alquiler de equipo", costo_base)
        if not isinstance(tipo_equipo, str) or not tipo_equipo.strip():
            raise ServicioInvalidoError("Debe especificar el tipo de equipo.")
        self._tipo_equipo = tipo_equipo.strip()

    @property
    def tipo_equipo(self):
        return self._tipo_equipo

    def validar_parametros(self, **kwargs):
        'Valida los parámetros específicos que requiere este servicio.'
        unidades = kwargs.get("unidades")
        if isinstance(unidades, bool) or not isinstance(unidades, int) or unidades <= 0:
            raise ServicioInvalidoError("Las unidades deben ser un entero positivo.")
        return True

    def _factor_cantidad(self, **kwargs):
        'Calcula el multiplicador que depende de unidades o del nivel del servicio.'
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
        'Devuelve una descripción legible del servicio.'
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

# ============================================================================
# Módulo integrado: modelos/asesoria.py
# ============================================================================
"""Servicio especializado de asesoría con niveles tarifarios."""

class AsesoriaEspecializada(Servicio):
    # Claves normalizadas para aceptar variantes de acentos y mayúsculas.
    'Servicio especializado de asesoría; aplica un factor de precio según el nivel seleccionado.'
    NIVELES = {"Basico": 1.0, "Avanzado": 1.5, "Empresarial": 2.0}

    def __init__(self, identificador: str, costo_base: float, area_experticia: str):
        'Inicializa el objeto y valida o guarda sus datos iniciales.'
        super().__init__(identificador, "Asesoría especializada", costo_base)
        if not isinstance(area_experticia, str) or not area_experticia.strip():
            raise ServicioInvalidoError("Debe especificar el área de experticia.")
        self._area_experticia = area_experticia.strip()

    @property
    def area_experticia(self) -> str:
        return self._area_experticia

    @classmethod
    def _normalizar_nivel(cls, nivel) -> str:
        'Normaliza el texto del nivel y comprueba que sea una opción permitida.'
        if not isinstance(nivel, str):
            raise ServicioInvalidoError("El nivel de asesoría debe ser texto.")
        texto = unicodedata.normalize("NFD", nivel.strip())
        texto = "".join(caracter for caracter in texto if unicodedata.category(caracter) != "Mn")
        texto = texto.capitalize()
        if texto not in cls.NIVELES:
            raise ServicioInvalidoError(
                f"Nivel inválido: {nivel}. Opciones: Básico, Avanzado o Empresarial."
            )
        return texto

    def validar_parametros(self, **kwargs) -> bool:
        'Valida los parámetros específicos que requiere este servicio.'
        self._normalizar_nivel(kwargs.get("nivel", "Basico"))
        return True

    def _factor_cantidad(self, **kwargs) -> float:
        'Calcula el multiplicador que depende de unidades o del nivel del servicio.'
        nivel = self._normalizar_nivel(kwargs.get("nivel", "Basico"))
        return self.NIVELES[nivel]

    def calcular_costo(
        self, duracion: float, descuento: float = 0.0,
        aplicar_impuesto: bool = True, **kwargs
    ) -> float:
        """Sobrescribe el cálculo para validar el nivel de asesoría."""
        self.validar_parametros(**kwargs)
        return super().calcular_costo(
            duracion, descuento, aplicar_impuesto, **kwargs
        )

    def describir_servicio(self) -> str:
        'Devuelve una descripción legible del servicio.'
        return f"Asesoría en {self.area_experticia} (ID: {self.identificador})."

    def obtener_detalles(self) -> dict:
        """Devuelve los datos del servicio de asesoría especializada."""
        return {
            "tipo": "AsesoriaEspecializada",
            "id": self.identificador,
            "nombre": self.nombre_servicio,
            "costo_base": self.costo_base,
            "area_experticia": self.area_experticia,
        }


# ============================================================================
# Módulo integrado: modelos/reserva.py
# ============================================================================
"""Reserva con estados controlados y manejo avanzado de excepciones."""

class EstadoReserva(Enum):
    'Enumeración con los estados válidos que puede tener una reserva.'
    PENDIENTE = "Pendiente"
    CONFIRMADA = "Confirmada"
    FALLIDA = "Fallida"
    CANCELADA = "Cancelada"


class Reserva(EntidadBase):
    'Representa una reserva vinculada a un cliente y un servicio, con duración, parámetros, estado y costo.'
    def __init__(
        self, identificador, cliente, servicio, duracion,
        parametros_servicio=None, descuento=0.0, aplicar_impuesto=True
    ):
        'Inicializa el objeto y valida o guarda sus datos iniciales.'
        try:
            super().__init__(identificador)
        except (ValueError, TypeError) as exc:
            raise ReservaInvalidaError(
                "El identificador de la reserva es obligatorio."
            ) from exc

        # Importaciones locales para evitar dependencias circulares.

        if not isinstance(cliente, Cliente):
            raise ReservaInvalidaError("La reserva debe asociarse a un Cliente válido.")
        if not isinstance(servicio, Servicio):
            raise ReservaInvalidaError("La reserva debe asociarse a un Servicio válido.")
        if parametros_servicio is not None and not isinstance(parametros_servicio, dict):
            raise ReservaInvalidaError("Los parámetros del servicio deben proporcionarse como diccionario.")

        self._cliente = cliente
        self._servicio = servicio
        self._duracion = duracion
        self._parametros_servicio = dict(parametros_servicio or {})
        self._descuento = descuento
        self._aplicar_impuesto = aplicar_impuesto
        self._estado = EstadoReserva.PENDIENTE
        self._costo_total = None

    @property
    def cliente(self):
        return self._cliente

    @property
    def servicio(self):
        return self._servicio

    @property
    def duracion(self):
        return self._duracion

    @property
    def estado(self):
        return self._estado

    @property
    def costo_total(self):
        return self._costo_total

    def confirmar(self):
        'Valida y confirma una reserva pendiente; registra los errores y actualiza su estado.'
        logging.info("Iniciando confirmación de reserva %s.", self.identificador)

        # La validación de transición va fuera del bloque que marca FALLIDA.
        # Así, un intento inválido no transforma por error una reserva cancelada.
        if self.estado is not EstadoReserva.PENDIENTE:
            mensaje = (
                "Solo se puede confirmar una reserva pendiente. "
                f"Estado actual: {self.estado.value}."
            )
            logging.warning("No se pudo confirmar la reserva %s: %s", self.identificador, mensaje)
            raise ReservaInvalidaError(mensaje)

        # try contiene las validaciones y cálculos que podrían generar excepciones.
        try:
            self.servicio.validar_parametros(**self._parametros_servicio)
            costo = self.servicio.calcular_costo(
                self.duracion,
                descuento=self._descuento,
                aplicar_impuesto=self._aplicar_impuesto,
                **self._parametros_servicio
            )
        # Los errores conocidos se encadenan para conservar la causa original.
        except SoftwareFJError as exc:
            self._estado = EstadoReserva.FALLIDA
            logging.exception("No se pudo confirmar la reserva %s.", self.identificador)
            raise ReservaInvalidaError(
                f"No se pudo confirmar la reserva {self.identificador}: {exc}"
            ) from exc
        except Exception as exc:
            self._estado = EstadoReserva.FALLIDA
            logging.exception("Error inesperado en reserva %s.", self.identificador)
            raise ReservaInvalidaError(
                f"Error inesperado al procesar la reserva {self.identificador}."
            ) from exc
        # else se ejecuta solamente si la validación y el cálculo terminaron bien.
        else:
            self._costo_total = costo
            self._estado = EstadoReserva.CONFIRMADA
            logging.info(
                "Reserva %s confirmada. Total: %.2f.",
                self.identificador, self._costo_total
            )
            return self._costo_total
        # finally se ejecuta tanto si la operación termina bien como si falla.
        finally:
            logging.info(
                "Finalizó confirmación de %s. Estado: %s.",
                self.identificador, self.estado.value
            )

    def procesar(self):
        """Procesa la reserva y devuelve el costo total al confirmarla.

        Este método ofrece el punto de entrada explícito solicitado para
        procesar una reserva y reutiliza las validaciones de confirmar().
        """
        logging.info("Procesando reserva %s.", self.identificador)
        return self.confirmar()

    def cancelar(self):
        'Cancela una reserva confirmada; rechaza los demás estados.'
        if self.estado is not EstadoReserva.CONFIRMADA:
            mensaje = (
                "Solo se puede cancelar una reserva confirmada. "
                f"Estado actual: {self.estado.value}."
            )
            logging.warning("No se pudo cancelar la reserva %s: %s", self.identificador, mensaje)
            raise ReservaInvalidaError(mensaje)
        self._estado = EstadoReserva.CANCELADA
        logging.info("Reserva %s cancelada.", self.identificador)

    def obtener_detalles(self):
        'Devuelve los datos principales del objeto en forma de diccionario.'
        return {
            "tipo": "Reserva",
            "id": self.identificador,
            "cliente": self.cliente.nombre,
            "servicio": self.servicio.nombre_servicio,
            "duracion": self.duracion,
            "estado": self.estado.value,
            "costo_total": self.costo_total,
        }

    def __str__(self):
        costo = "Pendiente" if self.costo_total is None else f"${self.costo_total:,.2f}"
        return (
            f"{self.identificador} | {self.cliente.nombre} | "
            f"{self.servicio.nombre_servicio} | {self.estado.value} | {costo}"
        )

