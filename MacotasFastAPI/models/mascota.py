from pydantic import BaseModel
from typing import Optional, List
from enum import Enum


class Especie(str, Enum):
    PERRO = "PERRO"
    GATO = "GATO"
    HURON = "HURON"
    ROEDOR = "ROEDOR"
    OTRO = "OTRO"


class Estado(str, Enum):
    PERDIDO = "PERDIDO"
    ENCONTRADO = "ENCONTRADO"


class Color(str, Enum):
    NEGRO = "NEGRO"
    BLANCO = "BLANCO"
    CAFE = "CAFE"
    DORADO = "DORADO"
    GRIS = "GRIS"
    NARANJA = "NARANJA"
    BEIGE = "BEIGE"
    ROJIZO = "ROJIZO"
    MANCHADO = "MANCHADO"
    OTRO = "OTRO"


class Tamano(str, Enum):
    PEQUENO = "PEQUENO"
    MEDIANO = "MEDIANO"
    GRANDE = "GRANDE"


class Pelaje(str, Enum):
    CORTO = "CORTO"
    LARGO = "LARGO"
    RIZADO = "RIZADO"
    SIN_PELO = "SIN_PELO"


class RangoEdad(str, Enum):
    CACHORRO = "CACHORRO"
    JOVEN = "JOVEN"
    ADULTO = "ADULTO"
    MAYOR = "MAYOR"
    NO_SE = "NO_SE"


class MascotaInput(BaseModel):
    """Refleja exactamente la entidad Mascotas.java (mascotas service, puerto 8082)."""
    id: Optional[int] = None
    nombre: Optional[str] = None
    especie: Optional[Especie] = None
    estado: Optional[Estado] = None
    raza: Optional[str] = None
    color: Optional[Color] = None
    tamano: Optional[Tamano] = None
    pelaje: Optional[Pelaje] = None
    edad: Optional[int] = None
    rangoEdad: Optional[RangoEdad] = None
    senas: Optional[List[str]] = None
    descripcion: Optional[str] = None
    usuarioId: Optional[int] = None

    class Config:
        use_enum_values = True


class MatchRequest(BaseModel):
    mascota_perdida: MascotaInput
    candidatas: List[MascotaInput]


class MatchResult(BaseModel):
    mascota_id: Optional[int]
    score: float
    porcentaje: int
    detalle: dict
    alerta: bool
    mensaje: str
