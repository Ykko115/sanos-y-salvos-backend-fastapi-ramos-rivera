# prueba rapida del motor de similitud, ejecutar desde la raiz: python test_similitud.py

import sys
import asyncio
sys.path.insert(0, ".")

from models.mascota import MascotaInput as MascotaSchema
from services.similitud import comparar_descripcion

CASOS = [
    # descripcion_perdida, descripcion_candidata, resultado_esperado
    (
        "perro labrador color dorado, muy amigable",
        "labrador amarillo, juguetón",
        "MEDIO (>0.50)",
    ),
    (
        "gato negro con mancha blanca en el pecho",
        "gato siamés ojos azules",
        "BAJO  (<0.58)",
    ),
    (
        "perro pequeño, chihuahua, color café",
        "chihuahua marrón, orejas grandes",
        "MEDIO (>0.48)",
    ),
    (
        "pug de color negro, pasado de peso, mancha blanca en el pecho",
        "pug negro con manchas blancas, un poco gordito",
        "MUY ALTO (>0.70)",
    ),
    (
        "border collie blanco y negro, muy activo",
        "gato persa gris, tranquilo y dormilón",
        "MUY BAJO (<0.30)",
    ),
]


async def main() -> None:
    print("\n=== Test de similitud local (sentence-transformers) ===\n")
    print(f"{'Score':>7}  {'Esperado':<20}  Descripción A  →  Descripción B")
    print("─" * 90)

    for desc_a, desc_b, esperado in CASOS:
        m1 = MascotaSchema(descripcion=desc_a)
        m2 = MascotaSchema(descripcion=desc_b)
        score = await comparar_descripcion(m1, m2)

        etiqueta = "✓" if _cumple(score, esperado) else "✗"
        print(f"  {etiqueta} {score:.4f}  {esperado:<20}  '{desc_a}'  →  '{desc_b}'")

    print()


def _cumple(score: float, esperado: str) -> bool:
    import re
    m = re.search(r'([<>])(\d+\.\d+)', esperado)
    if m:
        op, val = m.group(1), float(m.group(2))
        return score > val if op == '>' else score < val
    return True


if __name__ == "__main__":
    asyncio.run(main())
