from typing import Optional, List
from Levenshtein import distance as levenshtein_distance
from models.mascota import MascotaInput, MatchResult, RangoEdad, Tamano
from services import similitud


# pesos: especie 0.35, raza 0.25, color 0.10, rangoEdad 0.10,
# tamano 0.07, senas 0.05, pelaje 0.03, descripcion*0.05

def _score_raza(raza_a: Optional[str], raza_b: Optional[str]) -> float:
    if not raza_a or not raza_b:
        return 0.0
    a, b = raza_a.lower().strip(), raza_b.lower().strip()
    if a == b:
        return 0.25
    max_len = max(len(a), len(b), 1)
    return round(0.25 * max(1.0 - levenshtein_distance(a, b) / max_len, 0.0), 4)


def _score_color(color_a: Optional[str], color_b: Optional[str]) -> float:
    if not color_a or not color_b:
        return 0.0
    return 0.10 if color_a == color_b else 0.0


def _score_tamano(tamano_a: Optional[str], tamano_b: Optional[str]) -> float:
    if not tamano_a or not tamano_b:
        return 0.0
    orden = {Tamano.PEQUENO: 0, Tamano.MEDIANO: 1, Tamano.GRANDE: 2}
    try:
        diff = abs(orden[Tamano(tamano_a)] - orden[Tamano(tamano_b)])
    except (ValueError, KeyError):
        return 0.0
    if diff == 0:
        return 0.07
    if diff == 1:
        return 0.035
    return 0.0


def _score_pelaje(pelaje_a: Optional[str], pelaje_b: Optional[str]) -> float:
    if not pelaje_a or not pelaje_b:
        return 0.0
    return 0.03 if pelaje_a == pelaje_b else 0.0


_RANGO_ORDEN = {
    RangoEdad.CACHORRO: 0,
    RangoEdad.JOVEN:    1,
    RangoEdad.ADULTO:   2,
    RangoEdad.MAYOR:    3,
}


def _score_rango_edad(rango_a: Optional[str], rango_b: Optional[str]) -> float:
    if not rango_a or not rango_b:
        return 0.0
    try:
        ra, rb = RangoEdad(rango_a), RangoEdad(rango_b)
    except ValueError:
        return 0.0
    if ra == RangoEdad.NO_SE or rb == RangoEdad.NO_SE:
        return 0.0
    diff = abs(_RANGO_ORDEN[ra] - _RANGO_ORDEN[rb])
    if diff == 0:
        return 0.10
    if diff == 1:
        return 0.05
    if diff == 2:
        return 0.02
    return 0.0


def _score_senas(senas_a: Optional[List[str]], senas_b: Optional[List[str]]) -> float:
    set_a = set(senas_a) if senas_a else set()
    set_b = set(senas_b) if senas_b else set()
    if not set_a or not set_b:
        return 0.0
    union = set_a | set_b
    return round(0.05 * len(set_a & set_b) / len(union), 4)


def _score_edad(edad_a: Optional[int], edad_b: Optional[int]) -> float:
    # fallback si no hay rangoEdad, tolera 1 año de diferencia
    if edad_a is None or edad_b is None:
        return 0.0
    diff = abs(edad_a - edad_b)
    if diff == 0:
        return 0.10
    if diff == 1:
        return 0.05
    return 0.0


def _mensaje(score: float, porcentaje: int) -> str:
    if score >= 0.85:
        return f"Alta coincidencia ({porcentaje}%): podria ser tu mascota, revisa los detalles."
    if score >= 0.65:
        return f"Posible coincidencia del {porcentaje}%: podria ser tu mascota, revisa los detalles."
    if score >= 0.40:
        return f"Coincidencia del {porcentaje}%: algunas caracteristicas similares."
    return f"Sin coincidencia significativa ({porcentaje}%)."


async def comparar(perdida: MascotaInput, candidata: MascotaInput) -> MatchResult:
    # calcula el score total entre dos mascotas, retorna 0 si la especie no coincide
    detalle: dict = {
        "especie": False,
        "raza": False,      "score_raza": 0.0,
        "color": False,     "score_color": 0.0,
        "tamano": False,    "score_tamano": 0.0,
        "pelaje": False,    "score_pelaje": 0.0,
        "rangoEdad": False, "score_rangoEdad": 0.0,
        "senas": False,     "score_senas": 0.0,
        "score_descripcion": 0.0,
    }

    # si la especie no coincide retorna score 0 directamente
    if not perdida.especie or not candidata.especie or perdida.especie != candidata.especie:
        return MatchResult(
            mascota_id=candidata.id,
            score=0.0,
            porcentaje=0,
            detalle=detalle,
            alerta=False,
            mensaje="Sin coincidencia: especies diferentes.",
        )

    score = 0.35
    detalle["especie"] = True

    # raza
    sr = _score_raza(perdida.raza, candidata.raza)
    score += sr
    detalle["raza"] = sr >= 0.10
    detalle["score_raza"] = sr

    # color
    sc = _score_color(perdida.color, candidata.color)
    score += sc
    detalle["color"] = sc > 0
    detalle["score_color"] = sc

    # rango de edad, si no hay usa edad exacta como fallback
    sre = _score_rango_edad(perdida.rangoEdad, candidata.rangoEdad)
    if sre == 0.0:
        sre = _score_edad(perdida.edad, candidata.edad)
    score += sre
    detalle["rangoEdad"] = sre > 0
    detalle["score_rangoEdad"] = sre

    # tamaño
    st = _score_tamano(perdida.tamano, candidata.tamano)
    score += st
    detalle["tamano"] = st > 0
    detalle["score_tamano"] = st

    # señas
    ss = _score_senas(perdida.senas, candidata.senas)
    score += ss
    detalle["senas"] = ss > 0
    detalle["score_senas"] = ss

    # pelaje
    sp = _score_pelaje(perdida.pelaje, candidata.pelaje)
    score += sp
    detalle["pelaje"] = sp > 0
    detalle["score_pelaje"] = sp

    # descripcion
    sd = await similitud.comparar_descripcion(perdida, candidata)
    score += sd * 0.05
    detalle["score_descripcion"] = round(sd, 4)

    score_final = round(min(score, 1.0), 4)
    porcentaje = int(score_final * 100)

    return MatchResult(
        mascota_id=candidata.id,
        score=score_final,
        porcentaje=porcentaje,
        detalle=detalle,
        alerta=score_final >= 0.60,
        mensaje=_mensaje(score_final, porcentaje),
    )
