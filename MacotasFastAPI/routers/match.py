import asyncio
from typing import List

from fastapi import APIRouter, HTTPException
from models.mascota import MatchRequest, MatchResult
from services.comparador import comparar

router = APIRouter()


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
