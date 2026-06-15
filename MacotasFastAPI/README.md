# mascota-matcher

Microservicio FastAPI que actúa como motor de coincidencias para el proyecto **Sanos y Salvos**.
Compara mascotas perdidas con mascotas encontradas usando atributos estructurados + IA (Claude).

## Arquitectura

```
Spring Boot (reportes:8083) ──POST /api/match──► FastAPI (mascota-matcher:8000)
                                                      │
                                              comparador.py (75%)
                                              claude_agent.py (25%)
                                                      │
                                              ◄── List[MatchResult]
```

## Instalación

```bash
# 1. Clonar / copiar la carpeta
cd mascota-matcher

# 2. Crear entorno virtual
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Editar .env y poner tu ANTHROPIC_API_KEY

# 5. Ejecutar
uvicorn main:app --reload --port 8000
```

## Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/match` | Recibe `MatchRequest`, retorna `List[MatchResult]` ordenado por score |
| GET | `/api/health` | Verifica que el servicio esté activo |

Documentación interactiva disponible en `http://localhost:8000/docs`.

## Lógica de scoring

| Componente | Peso | Criterio |
|-----------|------|---------|
| Especie | 0.35 | Coincidencia exacta (descarte si no coincide) |
| Raza | 0.25 | Fuzzy matching con distancia de Levenshtein |
| Edad | 0.15 | Exacta = 0.15, ±1 año = 0.075 |
| Claude (descripción) | ×0.25 | Score de similitud textual 0.0–1.0 |

**Score final** = score_comparador + (claude_score × 0.25) → máx 1.0  
**Alerta** = `true` si score_final ≥ 0.90

## Integración con Spring Boot

Agrega en `application.properties` del servicio **reportes**:

```properties
matcher.service.url=http://localhost:8000
```

Inyecta `MascotaMatchClient.java` (incluido en el proyecto) en `ReportesServiceImpl` para buscar coincidencias automáticamente al crear un reporte de tipo `ENCONTRADO`.

## Ejemplo de request

Ver `ejemplo_request.json`. Prueba rápida con curl:

```bash
curl -X POST http://localhost:8000/api/match \
  -H "Content-Type: application/json" \
  -d @ejemplo_request.json
```

Respuesta esperada (ordenada por score desc):

```json
[
  {
    "mascota_id": 2,
    "score": 0.9875,
    "detalle": {
      "especie": true,
      "raza": true,
      "score_raza": 0.25,
      "edad": true,
      "score_edad": 0.15,
      "claude_score": 0.85
    },
    "alerta": true
  },
  ...
]
```
