# compara descripciones usando embeddings y fuzzy matching
import re
import logging
import asyncio
from typing import Optional

from Levenshtein import distance as levenshtein_distance
from models.mascota import MascotaInput

logger = logging.getLogger(__name__)

_model = None

COLORES: set = {
    "negro", "negra", "blanco", "blanca",
    "marrón", "marron", "café", "cafe",
    "dorado", "dorada", "miel",
    "gris", "naranja",
    "atigrado", "atigrada",
    "manchado", "manchada",
    "tricolor", "beige", "crema",
    "rojizo", "rojiza", "castaño", "castana",
}

STOPWORDS_ES: set = {
    "el", "la", "los", "las", "un", "una", "unos", "unas",
    "de", "del", "al", "en", "y", "o", "que", "con",
    "se", "su", "sus", "es", "son", "está", "esta",
    "muy", "tiene", "poco", "algo", "este", "estos", "estas",
    "por", "para", "como", "pero", "más", "sin", "no", "si",
    "también", "hay", "fue", "era", "ser", "han",
}


def _get_model():
    # carga el modelo solo la primera vez
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        logger.info("Cargando paraphrase-multilingual-MiniLM-L12-v2 (primera vez ~120 MB)…")
        _model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
        logger.info("Modelo sentence-transformers listo.")
    return _model


def _tokenizar(texto: str) -> list:
    tokens = re.findall(r"\b[a-záéíóúüñ]+\b", texto.lower())
    return [t for t in tokens if t not in STOPWORDS_ES and len(t) > 2]


def _similitud_semantica(desc_a: str, desc_b: str) -> float:
    from sentence_transformers import util
    model = _get_model()
    emb_a = model.encode(desc_a, convert_to_tensor=True)
    emb_b = model.encode(desc_b, convert_to_tensor=True)
    return max(0.0, float(util.cos_sim(emb_a, emb_b).item()))


def _similitud_fuzzy(desc_a: str, desc_b: str) -> float:
    palabras_a = _tokenizar(desc_a)
    palabras_b = _tokenizar(desc_b)
    if not palabras_a or not palabras_b:
        return 0.0
    scores = []
    for pa in palabras_a:
        mejor = max(
            1.0 - levenshtein_distance(pa, pb) / max(len(pa), len(pb), 1)
            for pb in palabras_b
        )
        scores.append(mejor)
    return sum(scores) / len(scores)


def _similitud_colores(desc_a: str, desc_b: str) -> float:
    # similitud por colores usando jaccard, neutro si no hay colores
    colores_a = set(_tokenizar(desc_a)) & COLORES
    colores_b = set(_tokenizar(desc_b)) & COLORES
    if not colores_a and not colores_b:
        return 0.5
    if not colores_a or not colores_b:
        return 0.3
    return len(colores_a & colores_b) / len(colores_a | colores_b)


def _calcular_sync(desc_a: str, desc_b: str) -> float:
    semantica = _similitud_semantica(desc_a, desc_b)
    fuzzy = _similitud_fuzzy(desc_a, desc_b)
    colores = _similitud_colores(desc_a, desc_b)
    return round(min((semantica * 0.60) + (fuzzy * 0.25) + (colores * 0.15), 1.0), 4)


async def comparar_descripcion(perdida: MascotaInput, candidata: MascotaInput) -> float:
    # retorna 0.5 si alguna descripcion esta vacia, sino compara en thread pool
    try:
        desc_a = (perdida.descripcion or "").strip()
        desc_b = (candidata.descripcion or "").strip()
        if not desc_a or not desc_b:
            return 0.5
        return await asyncio.to_thread(_calcular_sync, desc_a, desc_b)
    except Exception as e:
        logger.error(f"Error en comparación de descripciones: {e}")
        return 0.5
