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

# ============================================================================
# Módulo integrado: modelos/asesoria.py
# ============================================================================
"""Servicio especializado de asesoría con niveles tarifarios."""

class AsesoriaEspecializada(Servicio):
    # Claves normalizadas para aceptar variantes de acentos y mayúsculas.
    NIVELES = {"Basico": 1.0, "Avanzado": 1.5, "Empresarial": 2.0}

    def __init__(self, identificador: str, costo_base: float, area_experticia: str = "General"):
        super().__init__(identificador, "Asesoría especializada", costo_base)
        if not isinstance(area_experticia, str) or not area_experticia.strip():
            area_experticia = "General"
        self._area_experticia = area_experticia.strip()

    @property
    def area_experticia(self) -> str:
        return self._area_experticia

    @classmethod
    def _normalizar_nivel(cls, nivel) -> str:
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
        self._normalizar_nivel(kwargs.get("nivel", "Basico"))
        return True

    def _factor_cantidad(self, **kwargs) -> float:
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
    PENDIENTE = "Pendiente"
    CONFIRMADA = "Confirmada"
    FALLIDA = "Fallida"
    CANCELADA = "Cancelada"


class Reserva(EntidadBase):
    def __init__(
        self, identificador, cliente, servicio, duracion,
        parametros_servicio=None, descuento=0.0, aplicar_impuesto=True
    ):
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

        try:
            self.servicio.validar_parametros(**self._parametros_servicio)
            costo = self.servicio.calcular_costo(
                self.duracion,
                descuento=self._descuento,
                aplicar_impuesto=self._aplicar_impuesto,
                **self._parametros_servicio
            )
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
        else:
            self._costo_total = costo
            self._estado = EstadoReserva.CONFIRMADA
            logging.info(
                "Reserva %s confirmada. Total: %.2f.",
                self.identificador, self._costo_total
            )
            return self._costo_total
        finally:
            logging.info(
                "Finalizó confirmación de %s. Estado: %s.",
                self.identificador, self.estado.value
            )

    def cancelar(self):
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

# ============================================================================
# Módulo integrado: servicios/gestor_sistema.py
# ============================================================================
"""Capa de gestión: administra listas internas y reglas del sistema."""

class GestorSistema:
    """Gestiona clientes, servicios y reservas sin utilizar una base de datos."""

    def __init__(self):
        self._clientes = []
        self._servicios = []
        self._reservas = []

    @property
    def clientes(self):
        return tuple(self._clientes)

    @property
    def servicios(self):
        return tuple(self._servicios)

    @property
    def reservas(self):
        return tuple(self._reservas)

    @staticmethod
    def _validar_unico(lista, identificador, tipo):
        if any(item.identificador.casefold() == identificador.casefold() for item in lista):
            mensaje = f"Ya existe un {tipo} con identificador '{identificador}'."
            logging.warning(mensaje)
            raise DuplicadoError(mensaje)

    @staticmethod
    def _validar_tipo(objeto, clase_esperada, etiqueta):
        if not isinstance(objeto, clase_esperada):
            mensaje = f"Se esperaba un objeto {etiqueta}."
            logging.warning(mensaje)
            raise TypeError(mensaje)

    def registrar_cliente(self, cliente: Cliente):
        self._validar_tipo(cliente, Cliente, "Cliente")
        self._validar_unico(self._clientes, cliente.identificador, "cliente")
        self._clientes.append(cliente)
        logging.info("Cliente registrado: %s.", cliente.identificador)
        return cliente

    def registrar_servicio(self, servicio: Servicio):
        self._validar_tipo(servicio, Servicio, "Servicio")
        self._validar_unico(self._servicios, servicio.identificador, "servicio")
        self._servicios.append(servicio)
        logging.info("Servicio registrado: %s.", servicio.identificador)
        return servicio

    def crear_reserva(self, reserva: Reserva):
        self._validar_tipo(reserva, Reserva, "Reserva")
        self._validar_unico(self._reservas, reserva.identificador, "reserva")

        cliente_registrado = next(
            (c for c in self._clientes if c is reserva.cliente), None
        )
        if cliente_registrado is None:
            mensaje = "El cliente asociado a la reserva no está registrado en el sistema."
            logging.warning(mensaje)
            raise ElementoNoEncontradoError(mensaje)

        servicio_registrado = next(
            (s for s in self._servicios if s is reserva.servicio), None
        )
        if servicio_registrado is None:
            mensaje = "El servicio asociado a la reserva no está registrado en el sistema."
            logging.warning(mensaje)
            raise ElementoNoEncontradoError(mensaje)

        self._reservas.append(reserva)
        logging.info("Reserva creada: %s.", reserva.identificador)
        return reserva

    @staticmethod
    def _buscar_por_id(lista, identificador, tipo):
        if not isinstance(identificador, str) or not identificador.strip():
            mensaje = f"El identificador para buscar {tipo} debe ser texto no vacío."
            logging.warning(mensaje)
            raise ElementoNoEncontradoError(mensaje)
        buscado = identificador.strip().casefold()
        for elemento in lista:
            if elemento.identificador.casefold() == buscado:
                return elemento
        mensaje = f"No existe el {tipo} '{identificador}'."
        logging.warning(mensaje)
        raise ElementoNoEncontradoError(mensaje)

    def buscar_cliente(self, identificador):
        return self._buscar_por_id(self._clientes, identificador, "cliente")

    def buscar_servicio(self, identificador):
        return self._buscar_por_id(self._servicios, identificador, "servicio")

    def buscar_reserva(self, identificador):
        return self._buscar_por_id(self._reservas, identificador, "reserva")


# ============================================================================
# Módulo integrado: utilidades/logging_config.py
# ============================================================================
"""Configuración centralizada de logs."""

def configurar_logging():
    carpeta = Path(__file__).resolve().parent / "logs"
    carpeta.mkdir(parents=True, exist_ok=True)
    archivo = carpeta / "registro_eventos.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - [%(name)s] - %(message)s",
        handlers=[
            logging.FileHandler(archivo, encoding="utf-8"),
            logging.StreamHandler()
        ],
        force=True
    )

# ============================================================================
# Módulo integrado: interfaz/ventana_principal.py
# ============================================================================
"""Interfaz gráfica con Tkinter; la lógica de negocio vive en GestorSistema."""

class VentanaPrincipal:
    def __init__(self, root, gestor):
        self.root = root
        self.gestor = gestor
        root.title("Software FJ | Gestión de clientes, servicios y reservas")
        root.geometry("1050x680")
        root.minsize(900, 600)
        self._crear_interfaz()
        self._actualizar_tablas()

    def _crear_interfaz(self):
        encabezado = ttk.Frame(self.root, padding=12)
        encabezado.pack(fill="x")
        ttk.Label(encabezado, text="Software FJ", font=("Segoe UI", 20, "bold")).pack(anchor="w")
        ttk.Label(
            encabezado,
            text="Sistema integral de clientes, servicios y reservas (datos en memoria)"
        ).pack(anchor="w")

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=12, pady=8)

        self.tab_clientes = ttk.Frame(self.notebook, padding=12)
        self.tab_servicios = ttk.Frame(self.notebook, padding=12)
        self.tab_reservas = ttk.Frame(self.notebook, padding=12)
        self.tab_eventos = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(self.tab_clientes, text="Clientes")
        self.notebook.add(self.tab_servicios, text="Servicios")
        self.notebook.add(self.tab_reservas, text="Reservas")
        self.notebook.add(self.tab_eventos, text="Ayuda y logs")

        self._crear_tab_clientes()
        self._crear_tab_servicios()
        self._crear_tab_reservas()
        self._crear_tab_eventos()

    def _crear_tab_clientes(self):
        form = ttk.LabelFrame(self.tab_clientes, text="Registrar cliente", padding=10)
        form.pack(fill="x")
        self.c_id = tk.StringVar()
        self.c_nombre = tk.StringVar()
        self.c_correo = tk.StringVar()
        self.c_telefono = tk.StringVar()
        campos = [("Identificador", self.c_id), ("Nombre", self.c_nombre),
                  ("Correo", self.c_correo), ("Teléfono", self.c_telefono)]
        for i, (texto, variable) in enumerate(campos):
            ttk.Label(form, text=texto).grid(row=i // 2, column=(i % 2) * 2, sticky="w", padx=5, pady=5)
            ttk.Entry(form, textvariable=variable, width=32).grid(
                row=i // 2, column=(i % 2) * 2 + 1, sticky="ew", padx=5, pady=5
            )
        ttk.Button(form, text="Registrar cliente", command=self._registrar_cliente).grid(
            row=2, column=0, columnspan=4, sticky="ew", padx=5, pady=6
        )
        self.tabla_clientes = self._crear_tabla(
            self.tab_clientes, ("id", "nombre", "correo", "telefono"),
            ("ID", "Nombre", "Correo", "Teléfono")
        )

    def _crear_tab_servicios(self):
        form = ttk.LabelFrame(self.tab_servicios, text="Crear servicio", padding=10)
        form.pack(fill="x")
        self.s_id = tk.StringVar()
        self.s_tipo = tk.StringVar(value="Sala")
        self.s_costo = tk.StringVar()
        self.s_extra = tk.StringVar()

        ttk.Label(form, text="Identificador").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(form, textvariable=self.s_id, width=20).grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(form, text="Tipo").grid(row=0, column=2, sticky="w", padx=5, pady=5)
        selector_tipo = ttk.Combobox(
            form, textvariable=self.s_tipo, state="readonly",
            values=("Sala", "Equipo", "Asesoría"), width=18
        )
        selector_tipo.grid(row=0, column=3, padx=5, pady=5)
        ttk.Label(form, text="Costo base").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(form, textvariable=self.s_costo, width=20).grid(row=1, column=1, padx=5, pady=5)

        self.s_extra_label = ttk.Label(form, text="Capacidad de personas")
        self.s_extra_entry = ttk.Entry(form, textvariable=self.s_extra, width=25)
        self.s_extra_label.grid(row=1, column=2, sticky="w", padx=5, pady=5)
        self.s_extra_entry.grid(row=1, column=3, padx=5, pady=5)
        selector_tipo.bind("<<ComboboxSelected>>", self._actualizar_campos_servicio)

        ttk.Button(form, text="Crear servicio", command=self._crear_servicio).grid(
            row=3, column=0, columnspan=4, sticky="ew", padx=5, pady=6
        )
        self.tabla_servicios = self._crear_tabla(
            self.tab_servicios, ("id", "tipo", "costo", "descripcion"),
            ("ID", "Tipo", "Costo base", "Descripción")
        )
        self._actualizar_campos_servicio()

    def _actualizar_campos_servicio(self, *_):
        """Muestra capacidad únicamente cuando el tipo de servicio es Sala."""
        if self.s_tipo.get() == "Sala":
            self.s_extra_label.configure(text="Capacidad de personas")
            self.s_extra_label.grid()
            self.s_extra_entry.grid()
        else:
            self.s_extra_label.grid_remove()
            self.s_extra_entry.grid_remove()
            self.s_extra.set("")

    def _crear_tab_reservas(self):
        form = ttk.LabelFrame(self.tab_reservas, text="Gestión de reservas", padding=10)
        form.pack(fill="x")
        self.r_id = tk.StringVar()
        self.r_cliente = tk.StringVar()
        self.r_servicio = tk.StringVar()
        self.r_duracion = tk.StringVar(value="1")
        self.r_parametro = tk.StringVar(value="1")
        self.r_descuento = tk.StringVar(value="0")
        self.r_impuesto = tk.BooleanVar(value=True)
        campos = [
            ("ID reserva", self.r_id), ("ID cliente", self.r_cliente),
            ("ID servicio", self.r_servicio), ("Duración (horas/días)", self.r_duracion),
            ("Descuento ($)", self.r_descuento)
        ]
        for i, (texto, variable) in enumerate(campos):
            fila, col = divmod(i, 2)
            ttk.Label(form, text=texto).grid(row=fila, column=col * 2, sticky="w", padx=5, pady=4)
            ttk.Entry(form, textvariable=variable, width=27).grid(
                row=fila, column=col * 2 + 1, sticky="ew", padx=5, pady=4
            )

        self.r_parametro_label = ttk.Label(form, text="Parámetro (personas/unidades)")
        self.r_parametro_label.grid(row=2, column=0, sticky="w", padx=5, pady=4)
        self.r_parametro_entry = ttk.Entry(form, textvariable=self.r_parametro, width=27)
        self.r_parametro_combo = ttk.Combobox(
            form, textvariable=self.r_parametro, state="readonly",
            values=("Básico", "Avanzado", "Empresarial"), width=24
        )
        self.r_parametro_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=4)

        self.r_servicio.trace_add("write", self._actualizar_parametro_segun_servicio)
        ttk.Checkbutton(form, text="Aplicar impuesto (19 %)", variable=self.r_impuesto).grid(
            row=3, column=0, columnspan=2, sticky="w", padx=5, pady=4
        )
        botones = ttk.Frame(form)
        botones.grid(row=3, column=2, columnspan=2, sticky="ew", padx=5, pady=4)
        ttk.Button(botones, text="Crear reserva", command=self._crear_reserva).pack(side="left", padx=3)
        ttk.Button(botones, text="Confirmar seleccionada", command=self._confirmar_reserva).pack(side="left", padx=3)
        ttk.Button(botones, text="Cancelar seleccionada", command=self._cancelar_reserva).pack(side="left", padx=3)
        ttk.Button(botones, text="Actualizar", command=self._actualizar_tablas).pack(side="left", padx=3)
        self.tabla_reservas = self._crear_tabla(
            self.tab_reservas, ("id", "cliente", "servicio", "duracion", "estado", "costo"),
            ("ID", "Cliente", "Servicio", "Duración", "Estado", "Total")
        )
        ttk.Label(
            self.tab_reservas,
            text="Sala: número de personas | Equipo: número de unidades | Asesoría: seleccione Básico, Avanzado o Empresarial."
        ).pack(anchor="w", pady=5)

    def _actualizar_parametro_segun_servicio(self, *_):
        """Adapta el campo parámetro al tipo de servicio seleccionado."""
        identificador = self.r_servicio.get().strip().casefold()
        servicio = next(
            (item for item in self.gestor.servicios
             if item.identificador.casefold() == identificador),
            None,
        )
        if isinstance(servicio, AsesoriaEspecializada):
            self.r_parametro_label.configure(text="Nivel de asesoría")
            self.r_parametro_entry.grid_remove()
            self.r_parametro_combo.grid(row=2, column=1, sticky="ew", padx=5, pady=4)
            if self.r_parametro.get() not in ("Básico", "Avanzado", "Empresarial"):
                self.r_parametro.set("Básico")
        else:
            self.r_parametro_combo.grid_remove()
            self.r_parametro_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=4)
            if isinstance(servicio, ReservaSala):
                self.r_parametro_label.configure(text="Número de personas")
            elif isinstance(servicio, AlquilerEquipo):
                self.r_parametro_label.configure(text="Número de unidades")
            else:
                self.r_parametro_label.configure(text="Parámetro (personas/unidades)")
            if self.r_parametro.get() in ("Básico", "Avanzado", "Empresarial"):
                self.r_parametro.set("1")

    def _crear_tab_eventos(self):
        """Construye la sección de ayuda, simulación y administración de logs."""
        marco_simulacion = ttk.LabelFrame(
            self.tab_eventos, text="Simulación del sistema", padding=10
        )
        marco_simulacion.pack(fill="x", pady=5)
        ttk.Button(
            marco_simulacion,
            text="Ejecutar simulación de 16 operaciones",
            command=self._ejecutar_simulacion_interfaz
        ).pack(side="left", padx=5)
        ttk.Button(
            marco_simulacion,
            text="Limpiar resultados",
            command=self._limpiar_resultados_simulacion
        ).pack(side="left", padx=5)

        marco_logs = ttk.LabelFrame(
            self.tab_eventos, text="Administración de logs", padding=10
        )
        marco_logs.pack(fill="x", pady=5)
        ttk.Button(
            marco_logs, text="Generar log", command=self._generar_log
        ).pack(side="left", padx=5)
        ttk.Button(
            marco_logs, text="Abrir archivo log", command=self._mostrar_log
        ).pack(side="left", padx=5)
        ttk.Button(
            marco_logs, text="Mostrar ubicación", command=self._mostrar_ubicacion_log
        ).pack(side="left", padx=5)

        marco_resultados = ttk.LabelFrame(
            self.tab_eventos, text="Resultados de la simulación", padding=10
        )
        marco_resultados.pack(fill="both", expand=True, pady=8)
        self.txt_resultados = tk.Text(
            marco_resultados, height=14, wrap="word",
            font=("Consolas", 9), state="disabled"
        )
        self.txt_resultados.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(
            marco_resultados, orient="vertical", command=self.txt_resultados.yview
        )
        scrollbar.pack(side="right", fill="y")
        self.txt_resultados.configure(yscrollcommand=scrollbar.set)

        ttk.Label(
            self.tab_eventos,
            text="Para pruebas automatizadas ejecute: py -m unittest discover -s pruebas"
        ).pack(anchor="w", pady=5)

    def _ruta_log(self):
        return Path(__file__).resolve().parent / "logs" / "registro_eventos.log"

    def _agregar_resultado_simulacion(self, mensaje):
        self.txt_resultados.configure(state="normal")
        self.txt_resultados.insert("end", str(mensaje) + "\n")
        self.txt_resultados.see("end")
        self.txt_resultados.configure(state="disabled")

    def _limpiar_resultados_simulacion(self):
        self.txt_resultados.configure(state="normal")
        self.txt_resultados.delete("1.0", "end")
        self.txt_resultados.configure(state="disabled")

    def _ejecutar_simulacion_interfaz(self):
        self._limpiar_resultados_simulacion()
        self._agregar_resultado_simulacion("=" * 72)
        self._agregar_resultado_simulacion("INICIANDO SIMULACIÓN DEL SOFTWARE FJ")
        self._agregar_resultado_simulacion("=" * 72)
        try:
            ejecutar_simulacion(
                gestor=self.gestor,
                salida=self._agregar_resultado_simulacion,
                configurar=False
            )
            self._agregar_resultado_simulacion("\nSIMULACIÓN FINALIZADA.")
            self._agregar_resultado_simulacion(f"Archivo de registros: {self._ruta_log()}")
            messagebox.showinfo(
                "Simulación finalizada",
                "La simulación de 16 operaciones terminó.\n\n"
                "Puede consultar los resultados en esta pestaña y el detalle en el archivo de logs."
            )
        except Exception as exc:
            logging.exception("Error al ejecutar la simulación desde la interfaz.")
            self._agregar_resultado_simulacion(f"ERROR GENERAL: {exc}")
            messagebox.showerror("Error de simulación", str(exc))

    def _generar_log(self):
        try:
            ruta = self._ruta_log()
            ruta.parent.mkdir(parents=True, exist_ok=True)
            if not ruta.exists():
                ruta.touch(encoding="utf-8")
            logging.info("Archivo de log consultado desde la interfaz.")
            messagebox.showinfo("Archivo de logs", f"Archivo disponible en:\n{ruta}")
        except OSError as exc:
            messagebox.showerror("Error", f"No fue posible generar el archivo de log:\n{exc}")

    def _mostrar_ubicacion_log(self):
        messagebox.showinfo("Ubicación del log", str(self._ruta_log()))

    def _crear_tabla(self, parent, columnas, encabezados):
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True, pady=10)
        tree = ttk.Treeview(frame, columns=columnas, show="headings", height=12)
        for col, texto in zip(columnas, encabezados):
            tree.heading(col, text=texto)
            tree.column(col, width=140, anchor="w")
        scroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        return tree

    def _ejecutar_seguro(self, accion):
        try:
            accion()
            self._actualizar_tablas()
        except SoftwareFJError as exc:
            logging.warning("Operación rechazada desde interfaz: %s", exc)
            messagebox.showwarning("No se pudo completar", str(exc))
        except (ValueError, TypeError) as exc:
            logging.exception("Datos ingresados inválidos.")
            messagebox.showwarning("Datos inválidos", str(exc))
        except Exception:
            logging.exception("Error inesperado desde la interfaz.")
            messagebox.showerror(
                "Error inesperado",
                "La operación no se completó. Consulte logs/registro_eventos.log."
            )

    def _registrar_cliente(self):
        def accion():
            cliente = Cliente(
                self.c_id.get(), self.c_nombre.get(),
                self.c_correo.get(), self.c_telefono.get()
            )
            self.gestor.registrar_cliente(cliente)
            messagebox.showinfo("Software FJ", f"Cliente {cliente.nombre} registrado.")
        self._ejecutar_seguro(accion)

    def _crear_servicio(self):
        def accion():
            identificador = self.s_id.get()
            costo = float(self.s_costo.get())
            tipo = self.s_tipo.get()
            if tipo == "Sala":
                capacidad = int(self.s_extra.get())
                servicio = ReservaSala(identificador, costo, capacidad)
            elif tipo == "Equipo":
                servicio = AlquilerEquipo(identificador, costo)
            else:
                servicio = AsesoriaEspecializada(identificador, costo)
            self.gestor.registrar_servicio(servicio)
            messagebox.showinfo("Software FJ", f"Servicio creado: {servicio.describir_servicio()}")
        self._ejecutar_seguro(accion)

    def _crear_reserva(self):
        """Registra una reserva nueva y la deja en estado Pendiente."""
        def accion():
            cliente = self.gestor.buscar_cliente(self.r_cliente.get().strip())
            servicio = self.gestor.buscar_servicio(self.r_servicio.get().strip())
            duracion = float(self.r_duracion.get())
            descuento = float(self.r_descuento.get())
            parametro = self.r_parametro.get().strip()
            if isinstance(servicio, ReservaSala):
                parametros = {"personas": int(parametro)}
            elif isinstance(servicio, AlquilerEquipo):
                parametros = {"unidades": int(parametro)}
            elif isinstance(servicio, AsesoriaEspecializada):
                parametros = {"nivel": parametro or "Básico"}
            else:
                parametros = {}
            reserva = Reserva(
                self.r_id.get().strip(), cliente, servicio, duracion,
                parametros_servicio=parametros,
                descuento=descuento,
                aplicar_impuesto=self.r_impuesto.get()
            )
            self.gestor.crear_reserva(reserva)
            messagebox.showinfo(
                "Reserva creada",
                f"La reserva {reserva.identificador} fue creada correctamente.\nEstado: Pendiente.\n\nPara procesarla, selecciónela y pulse 'Confirmar seleccionada'."
            )
        self._ejecutar_seguro(accion)

    def _confirmar_reserva(self):
        """Confirma únicamente la reserva pendiente seleccionada en la tabla."""
        seleccion = self.tabla_reservas.selection()
        if not seleccion:
            messagebox.showinfo("Seleccionar reserva", "Seleccione una reserva pendiente en la tabla.")
            return
        identificador = self.tabla_reservas.item(seleccion[0], "values")[0]

        def accion():
            reserva = self.gestor.buscar_reserva(identificador)
            total = reserva.confirmar()
            messagebox.showinfo(
                "Reserva confirmada",
                f"Reserva {identificador} confirmada correctamente.\nTotal: ${total:,.2f}"
            )
        self._ejecutar_seguro(accion)

    def _cancelar_reserva(self):
        seleccion = self.tabla_reservas.selection()
        if not seleccion:
            messagebox.showinfo("Seleccionar reserva", "Seleccione una reserva en la tabla.")
            return
        identificador = self.tabla_reservas.item(seleccion[0], "values")[0]
        def accion():
            reserva = self.gestor.buscar_reserva(identificador)
            reserva.cancelar()
            messagebox.showinfo("Software FJ", f"Reserva {identificador} cancelada.")
        self._ejecutar_seguro(accion)

    def _actualizar_tablas(self):
        for tabla in (getattr(self, "tabla_clientes", None),
                      getattr(self, "tabla_servicios", None),
                      getattr(self, "tabla_reservas", None)):
            if tabla is not None:
                for item in tabla.get_children():
                    tabla.delete(item)
        if hasattr(self, "tabla_clientes"):
            for c in self.gestor.clientes:
                self.tabla_clientes.insert("", "end", values=(c.identificador, c.nombre, c.correo, c.telefono))
        if hasattr(self, "tabla_servicios"):
            for s in self.gestor.servicios:
                self.tabla_servicios.insert(
                    "", "end",
                    values=(s.identificador, s.nombre_servicio, f"${s.costo_base:,.2f}", s.describir_servicio())
                )
        if hasattr(self, "tabla_reservas"):
            for r in self.gestor.reservas:
                costo = "-" if r.costo_total is None else f"${r.costo_total:,.2f}"
                self.tabla_reservas.insert(
                    "", "end",
                    values=(r.identificador, r.cliente.nombre, r.servicio.nombre_servicio,
                            r.duracion, r.estado.value, costo)
                )

    def _mostrar_log(self):
        """Abre el archivo de logs con la aplicación predeterminada del sistema."""
        ruta = self._ruta_log()
        if not ruta.exists():
            messagebox.showinfo(
                "Archivo de logs",
                "Todavía no existe el archivo. Ejecute una operación o pulse Generar log."
            )
            return
        try:
            import os
            import subprocess
            import platform
            sistema = platform.system()
            if sistema == "Windows":
                os.startfile(str(ruta))
            elif sistema == "Darwin":
                subprocess.Popen(["open", str(ruta)])
            else:
                subprocess.Popen(["xdg-open", str(ruta)])
        except Exception as exc:
            logging.exception("No fue posible abrir el archivo de logs.")
            messagebox.showerror("No se pudo abrir", f"Abra el archivo manualmente:\n{ruta}\n\n{exc}")


# ============================================================================
# Simulación
# ============================================================================
"""Simulación de operaciones válidas e inválidas para evidenciar el manejo de excepciones."""

def intentar(etiqueta, funcion, salida=None):
    """Ejecuta un escenario y envía su resultado a consola o a la interfaz."""
    mostrar = salida if salida is not None else print
    mostrar(f"\n{etiqueta}")
    try:
        resultado = funcion()
    except SoftwareFJError as exc:
        logging.warning("%s: %s", etiqueta, exc)
        mostrar(f"ERROR CONTROLADO: {exc}")
    except Exception as exc:
        logging.exception("Error inesperado durante %s", etiqueta)
        mostrar(f"ERROR INESPERADO: {exc}")
    else:
        logging.info("%s. Resultado: %s", etiqueta, resultado)
        mostrar(f"RESULTADO EXITOSO: {resultado}")
    finally:
        mostrar("Operación finalizada.")
        mostrar("-" * 65)


def ejecutar_simulacion(gestor=None, salida=None, configurar=True):
    """Revisa 16 aspectos usando exclusivamente los datos reales del GestorSistema.

    No crea registros de prueba, no elimina información y no modifica reservas.
    Si no se proporciona un gestor (ejecución independiente por consola), se
    utiliza uno vacío y se informa que no hay información registrada.
    """
    if configurar:
        configurar_logging()

    mostrar = salida if salida is not None else print
    g = gestor if gestor is not None else GestorSistema()

    def exigir_registros(registros, tipo):
        if not registros:
            raise ElementoNoEncontradoError(
                f"No se encuentra información de {tipo}. Registre al menos uno para realizar esta validación."
            )
        return registros

    def validar_identificadores_unicos(registros, tipo):
        ids = [item.identificador.casefold() for item in registros]
        if len(ids) != len(set(ids)):
            raise DuplicadoError(f"Se encontraron identificadores duplicados en {tipo}.")
        return f"Los {tipo} tienen identificadores únicos ({len(ids)} registros)."

    def validar_relaciones_reservas():
        reservas = exigir_registros(g.reservas, "reservas")
        clientes = {id(item) for item in g.clientes}
        servicios = {id(item) for item in g.servicios}
        inconsistentes = [
            r.identificador for r in reservas
            if id(r.cliente) not in clientes or id(r.servicio) not in servicios
        ]
        if inconsistentes:
            raise ElementoNoEncontradoError(
                "Hay reservas asociadas a clientes o servicios que no están registrados: "
                + ", ".join(inconsistentes)
            )
        return f"Las {len(reservas)} reservas están asociadas a clientes y servicios registrados."

    def resumen_reservas(estado=None):
        reservas = exigir_registros(g.reservas, "reservas")
        if estado is None:
            return f"Total de reservas registradas: {len(reservas)}."
        cantidad = sum(1 for r in reservas if r.estado is estado)
        return f"Reservas en estado {estado.value}: {cantidad}."

    escenarios = [
        ("1. Comprobar existencia de clientes", lambda: f"Clientes encontrados: {len(exigir_registros(g.clientes, 'clientes'))}."),
        ("2. Consultar clientes registrados", lambda: " | ".join(str(c) for c in exigir_registros(g.clientes, 'clientes'))),
        ("3. Validar identificadores de clientes", lambda: validar_identificadores_unicos(g.clientes, "clientes")),
        ("4. Consultar primer cliente registrado", lambda: exigir_registros(g.clientes, "clientes")[0].obtener_detalles()),
        ("5. Comprobar existencia de servicios", lambda: f"Servicios encontrados: {len(exigir_registros(g.servicios, 'servicios'))}."),
        ("6. Consultar servicios registrados", lambda: " | ".join(s.describir_servicio() for s in exigir_registros(g.servicios, 'servicios'))),
        ("7. Validar identificadores de servicios", lambda: validar_identificadores_unicos(g.servicios, "servicios")),
        ("8. Consultar primer servicio registrado", lambda: exigir_registros(g.servicios, "servicios")[0].obtener_detalles()),
        ("9. Comprobar existencia de reservas", lambda: f"Reservas encontradas: {len(exigir_registros(g.reservas, 'reservas'))}."),
        ("10. Consultar reservas registradas", lambda: " | ".join(str(r) for r in exigir_registros(g.reservas, 'reservas'))),
        ("11. Consultar detalles de la primera reserva", lambda: exigir_registros(g.reservas, "reservas")[0].obtener_detalles()),
        ("12. Validar asociaciones de reservas", validar_relaciones_reservas),
        ("13. Resumen general de clientes", lambda: f"Total de clientes registrados: {len(exigir_registros(g.clientes, 'clientes'))}."),
        ("14. Resumen general de servicios", lambda: f"Total de servicios registrados: {len(exigir_registros(g.servicios, 'servicios'))}."),
        ("15. Resumen de reservas pendientes", lambda: resumen_reservas(EstadoReserva.PENDIENTE)),
        ("16. Resumen general de reservas", lambda: resumen_reservas()),
    ]

    mostrar("=" * 72)
    mostrar("REVISIÓN DE 16 OPERACIONES - DATOS REALES DE SOFTWARE FJ")
    mostrar("No se crearán ni modificarán registros durante esta revisión.")
    mostrar("=" * 72)
    mostrar(f"Registros actuales: {len(g.clientes)} clientes | {len(g.servicios)} servicios | {len(g.reservas)} reservas.")

    for etiqueta, funcion in escenarios:
        intentar(etiqueta, funcion, mostrar)

    mostrar("\nREVISIÓN DE LAS 16 OPERACIONES FINALIZADA.")
    mostrar("Los registros originales de la aplicación no fueron modificados.")
    mostrar(f"Archivo de registros: {Path(__file__).resolve().parent / 'logs' / 'registro_eventos.log'}")
    logging.info("Revisión de 16 operaciones sobre datos reales finalizada.")

# ============================================================================
# Inicio de la aplicación
# ============================================================================
def iniciar_interfaz():
    configurar_logging()
    gestor = GestorSistema()
    root = tk.Tk()
    try:
        VentanaPrincipal(root, gestor)
        root.mainloop()
    except SoftwareFJError as exc:
        logging.exception("Error controlado al iniciar la aplicación")
        messagebox.showerror("Software FJ", str(exc))
    except Exception:
        logging.exception("Error inesperado al iniciar la aplicación")
        messagebox.showerror(
            "Error inesperado",
            "No fue posible iniciar la aplicación. Revise logs/registro_eventos.log."
        )

if __name__ == "__main__":
    if "--simular" in sys.argv:
        ejecutar_simulacion()
    else:
        iniciar_interfaz()