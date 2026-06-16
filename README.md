# Sanos y Salvos — Backend FastAPI (Motor de Coincidencias)

Motor de coincidencias de mascotas y análisis de imágenes con IA para el proyecto **Sanos y Salvos**. Desarrollado con **Python + FastAPI** por **Nicolás Ramos** y **Alberto Rivera** — Instituto Profesional DUOC UC, FullStack 3.

---

## Descripción

Este servicio complementa los microservicios Spring Boot con dos capacidades especializadas:

1. **Matching de mascotas**: algoritmo de scoring ponderado que compara las características de una mascota perdida contra candidatas encontradas, retornando un porcentaje de coincidencia.
2. **Análisis de foto con IA**: clasifica la especie de una mascota a partir de una imagen usando modelos de Hugging Face (ViT + ResNet).

---

## Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/api/match` | Compara una mascota perdida contra una lista de candidatas |
| `GET`  | `/api/coincidencias` | Obtiene automáticamente todos los reportes desde Spring y calcula coincidencias (score ≥ 60) |
| `POST` | `/api/ia/analizar-foto` | Analiza una foto y retorna especie, raza, color, tamaño y confianza estimada |
| `GET`  | `/api/health` | Estado del servicio |

Documentación interactiva disponible en `http://localhost:8000/docs` (Swagger UI).

---

## Algoritmo de scoring

El endpoint `/api/match` compara dos mascotas usando los siguientes pesos:

| Criterio | Peso | Detalle |
|----------|------|---------|
| Especie | 35% | Requisito mínimo: si no coincide, score = 0 |
| Raza | 25% | Coincidencia exacta o aproximada (distancia Levenshtein) |
| Color | 10% | Coincidencia exacta por enum |
| Rango de edad | 10% | Tolerancia de ±1 rango (cachorro/joven/adulto/mayor) |
| Tamaño | 7% | Tolerancia de ±1 tamaño (pequeño/mediano/grande) |
| Señas | 5% | Jaccard entre listas de señas particulares |
| Descripción | 5% | Similitud semántica con Sentence Transformers |
| Pelaje | 3% | Coincidencia exacta por enum |

Una coincidencia genera **alerta** cuando el score es ≥ 60%.

El endpoint `/api/coincidencias` usa scoring simplificado sobre los reportes del sistema:

| Criterio | Puntos |
|----------|--------|
| Especie igual | +30 |
| Raza similar | +25 |
| Color igual | +20 |
| Dentro de 5 km | +15 |
| Dentro de 15 días | +10 |

Solo se retornan coincidencias con score ≥ 60 puntos.

---

## Stack tecnológico

| Tecnología | Versión | Uso |
|------------|---------|-----|
| Python | 3.13 | Lenguaje base |
| FastAPI | 0.110 | Framework web |
| Uvicorn | 0.27 | Servidor ASGI |
| Pydantic | ≥2.9 | Validación de datos |
| Sentence Transformers | 2.6 | Similitud semántica de descripciones |
| PyTorch | 2.6 | Backend de inferencia |
| python-Levenshtein | ≥0.25 | Distancia de edición para razas |
| httpx | 0.27 | Cliente HTTP asíncrono |
| python-dotenv | 1.0 | Variables de entorno |

---

## Requisitos previos

- Python 3.11+
- pip o virtualenv
- Token de Hugging Face (para el endpoint de análisis de foto)

---

## Instalación y ejecución

```bash
cd MacotasFastAPI

# Crear entorno virtual
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus tokens

# Ejecutar el servidor
uvicorn main:app --reload --port 8000
```

La API queda disponible en `http://localhost:8000`.

---

## Variables de entorno

```env
HF_TOKEN=hf_TuTokenDeHuggingFaceAqui   # Token de Hugging Face (para analizar-foto)
SPRING_URL=http://localhost:8080         # URL del API Gateway Spring Boot
JAVA_API=http://localhost:8080/api       # URL base de la API Java
```

---

## Ejecución con Docker

```bash
cd MacotasFastAPI
docker build -t fastapi-matcher:local .
docker run -p 8000:8000 --env-file .env fastapi-matcher:local
```

---

## Ejecutar tests

```bash
cd MacotasFastAPI
python -m pytest test_motor.py
python -m pytest test_similitud.py
```

---

## Estructura del proyecto

```
MacotasFastAPI/
├── main.py                  # App FastAPI, endpoint /api/ia/analizar-foto
├── routers/
│   └── match.py             # Endpoints /api/match y /api/coincidencias
├── models/
│   └── mascota.py           # Modelos Pydantic (MascotaInput, MatchRequest, MatchResult)
├── services/
│   ├── comparador.py        # Lógica de scoring ponderado
│   └── similitud.py         # Similitud semántica con Sentence Transformers
├── requirements.txt
├── Dockerfile
├── .env.example
├── test_motor.py
└── test_similitud.py
```

---

## Autores

- **Nicolás Ramos** — [@Ykko115](https://github.com/Ykko115)
- **Alberto Rivera**

Instituto Profesional DUOC UC — Carrera FullStack, 2026.
