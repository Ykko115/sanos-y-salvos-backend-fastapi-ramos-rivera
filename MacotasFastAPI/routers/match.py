import asyncio
import math
import os
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, HTTPException
from models.mascota import MatchRequest, MatchResult
from services.comparador import comparar

router = APIRouter()

SPRING_URL = os.getenv("SPRING_URL", "http://localhost:8080")


def _normalizar_reporte(raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not raw:
        return None
    reporte = raw.get("reporte") or raw
    mw = raw.get("mascota")
    md = None
    if mw:
        md = mw.get("mascota") or (mw if (mw.get("nombre") or mw.get("especie")) else None)
    ubicacion = reporte.get("ubicacion") or (md.get("ubicacion") if md else None) or raw.get("ubicacion")
    rid = reporte.get("id") or raw.get("id") or (md.get("id") if md else None) or reporte.get("reporteId")
    if rid is None:
        import random, time
        rid = f"{int(time.time())}_{random.random()}"

    return {
        "id": str(rid),
        "usuarioId": reporte.get("usuarioId") or raw.get("usuarioId") or (md.get("usuarioId") if md else None),
        "mascotaId": reporte.get("mascotaId") or raw.get("mascotaId") or (md.get("id") if md else None),
        "nombre": reporte.get("nombre_mascota") or (md.get("nombre") if md else None) or reporte.get("nombreMascota") or "Sin nombre",
        "especie": ((md.get("especie") if md else None) or (md.get("tipo") if md else None) or reporte.get("especie") or "").lower(),
        "raza": ((md.get("raza") if md else None) or reporte.get("raza") or "").lower(),
        "color": ((md.get("color") if md else None) or reporte.get("color") or "").lower(),
        "lat": (ubicacion.get("latitude") if ubicacion else None),
        "lng": (ubicacion.get("longitude") if ubicacion else None),
        "comuna": (md.get("comuna") if md else None) or (ubicacion.get("comuna") if ubicacion else None) or "",
        "fecha": reporte.get("fechaReporte") or (md.get("fecha_perdida") if md else None),
        "estado": ((reporte.get("estado") or (md.get("estado") if md else None) or raw.get("estado") or "")).upper(),
    }


def _distancia_km(lat1, lon1, lat2, lon2) -> float:
    R = 6371
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = math.sin(d_lat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


def _calcular_score(perdida: Dict, encontrada: Dict) -> Dict[str, Any]:
    score = 0
    criterios = []

    if perdida["especie"] and encontrada["especie"] and perdida["especie"] == encontrada["especie"]:
        score += 30
        criterios.append("especie")

    if perdida["raza"] and encontrada["raza"]:
        a, b = perdida["raza"], encontrada["raza"]
        if a == b or a in b or b in a:
            score += 25
            criterios.append("raza")

    if perdida["color"] and encontrada["color"]:
        a, b = perdida["color"], encontrada["color"]
        if a == b or a in b or b in a:
            score += 20
            criterios.append("color")

    if all(v is not None for v in [perdida["lat"], perdida["lng"], encontrada["lat"], encontrada["lng"]]):
        try:
            if _distancia_km(perdida["lat"], perdida["lng"], encontrada["lat"], encontrada["lng"]) <= 5:
                score += 15
                criterios.append("zona")
        except Exception:
            pass

    if perdida["fecha"] and encontrada["fecha"]:
        try:
            from datetime import datetime
            fmt = "%Y-%m-%dT%H:%M:%S" if "T" in str(perdida["fecha"]) else "%Y-%m-%d"
            fp = datetime.fromisoformat(str(perdida["fecha"]).split(".")[0])
            fe = datetime.fromisoformat(str(encontrada["fecha"]).split(".")[0])
            dias = abs((fp - fe).days)
            if dias <= 15:
                score += 10
                criterios.append("fecha")
        except Exception:
            pass

    return {"score": score, "criterios": criterios}


async def _fetch_coincidencias() -> List[Dict]:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{SPRING_URL}/api/reportes")
            resp.raise_for_status()
            data = resp.json()
    except Exception:
        return []

    if not isinstance(data, list) or not data:
        return []

    reportes = [r for r in (_normalizar_reporte(item) for item in data) if r]
    perdidas = [r for r in reportes if r["estado"] == "PERDIDO"]
    encontradas = [r for r in reportes if r["estado"] == "ENCONTRADO"]
    coincidencias = []

    for p in perdidas:
        for e in encontradas:
            resultado = _calcular_score(p, e)
            if resultado["score"] >= 60:
                coincidencias.append({
                    "id": f"match_{p['id']}_{e['id']}",
                    "score": resultado["score"],
                    "criterios": resultado["criterios"],
                    "mascota_perdida": p,
                    "mascota_encontrada": e,
                })

    coincidencias.sort(key=lambda c: c["score"], reverse=True)
    return coincidencias


@router.get("/coincidencias")
async def get_coincidencias() -> dict:
    coincidencias = await _fetch_coincidencias()
    return {"coincidencias": coincidencias}


@router.post("/match", response_model=List[MatchResult])
async def match_mascotas(request: MatchRequest) -> List[MatchResult]:
    # recibe mascota perdida y candidatas, retorna resultados ordenados por score
    if not request.candidatas:
        raise HTTPException(status_code=400, detail="La lista de candidatas no puede estar vacía")
    try:
        tareas = [comparar(request.mascota_perdida, c) for c in request.candidatas]
        resultados: List[MatchResult] = await asyncio.gather(*tareas)
        return sorted(resultados, key=lambda r: r.score, reverse=True)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno al procesar coincidencias: {str(e)}")


@router.get("/health")
async def health_check() -> dict:
    return {"status": "ok", "service": "mascota-matcher", "version": "1.0"}
