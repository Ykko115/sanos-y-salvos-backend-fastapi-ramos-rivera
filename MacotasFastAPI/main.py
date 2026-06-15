import logging
import os
import base64
import requests as req

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from routers.match import router as match_router

load_dotenv()
logging.basicConfig(level=logging.INFO)

HF_TOKEN = os.getenv("HF_TOKEN", "")

app = FastAPI(
    title="Mascota Matcher",
    description="Motor de coincidencias de mascotas — Sanos y Salvos",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://localhost:8082",
        "http://localhost:8083",
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:3001",
        "http://mascotas:8082",
        "http://reportes:8083",
        "http://apigateway:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(match_router, prefix="/api", tags=["match"])


@app.post("/api/ia/analizar-foto")
async def analizar_foto(file: UploadFile = File(...)):
    contenido = await file.read()
    img_b64 = base64.b64encode(contenido).decode()

    headers = {"Authorization": f"Bearer {HF_TOKEN}"}

    especie = "PERRO"
    raza = "No se"
    color = "OTRO"
    tamano = "MEDIANO"
    confianza = 0.0

    try:
        r = req.post(
            "https://api-inference.huggingface.co/models/google/vit-base-patch16-224",
            headers=headers,
            json={"inputs": img_b64},
            timeout=15,
        )
        resultados = r.json() if r.ok else []
        if isinstance(resultados, list) and resultados:
            label = resultados[0].get("label", "").lower()
            confianza = resultados[0].get("score", 0.0)
            if "cat" in label or "gato" in label or "kitten" in label:
                especie = "GATO"
            elif "ferret" in label:
                especie = "HURON"
            elif "hamster" in label or "mouse" in label or "rabbit" in label or "guinea" in label:
                especie = "ROEDOR"
            else:
                especie = "PERRO"
    except Exception:
        pass

    try:
        r2 = req.post(
            "https://api-inference.huggingface.co/models/julien-c/resnet-50",
            headers=headers,
            json={"inputs": img_b64},
            timeout=15,
        )
        res2 = r2.json() if r2.ok else []
        if isinstance(res2, list) and res2:
            raza = res2[0].get("label", "No se")
    except Exception:
        pass

    return {
        "especie": especie,
        "raza": raza,
        "color": color,
        "tamano": tamano,
        "confianza": round(confianza, 3),
    }


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "2.0.0"}


@app.on_event("startup")
async def startup_message():
    print("\n[OK] Motor de coincidencias listo en http://localhost:8000\n")
    print("  POST /api/match")
    print("  POST /api/ia/analizar-foto")
    print("  GET  /api/health")
    print("  Docs: http://localhost:8000/docs\n")
