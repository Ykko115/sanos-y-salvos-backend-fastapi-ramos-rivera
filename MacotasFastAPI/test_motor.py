# prueba del motor de coincidencias, ejecutar desde la raiz: python test_motor.py
import sys
import asyncio

sys.path.insert(0, ".")

from models.mascota import MascotaInput
from services.comparador import comparar

CASOS = [
    {
        "nombre": "Caso 1 — misma especie/raza, descripción similar  →  ALTO (> 0.85)",
        "perdida": MascotaInput(
            id=1, nombre="Luna", especie="PERRO", raza="Labrador", edad=3,
            descripcion="Perra labrador color dorado, muy amigable, sin collar. Se perdió en el parque.",
            estado="PERDIDO", usuarioId=1,
        ),
        "candidata": MascotaInput(
            id=2, nombre="Max", especie="PERRO", raza="Labrador", edad=3,
            descripcion="Labrador amarillo, muy cariñoso, sin collar. Encontrado cerca del parque.",
            estado="ENCONTRADO", usuarioId=2,
        ),
        "min": 0.85,
        "max": 1.0,
    },
    {
        "nombre": "Caso 2 — misma especie, raza y descripción distintas  →  MEDIO (0.40 – 0.65)",
        "perdida": MascotaInput(
            id=3, nombre="Negrito", especie="PERRO", raza="Pug", edad=8,
            descripcion="Pug negro, pasado de peso, mancha blanca en el pecho.",
            estado="PERDIDO", usuarioId=1,
        ),
        "candidata": MascotaInput(
            id=4, nombre="Canela", especie="PERRO", raza="Golden Retriever", edad=4,
            descripcion="Golden retriever color miel, juguetón, con collar rojo.",
            estado="ENCONTRADO", usuarioId=3,
        ),
        "min": 0.40,
        "max": 0.65,
    },
    {
        "nombre": "Caso 3 — especie diferente  →  SCORE 0 inmediato",
        "perdida": MascotaInput(
            id=5, nombre="Michi", especie="GATO", raza="Siamés", edad=2,
            descripcion="Gato siamés de ojos azules, muy tranquilo.",
            estado="PERDIDO", usuarioId=1,
        ),
        "candidata": MascotaInput(
            id=1, nombre="Black", especie="PERRO", raza="Pug", edad=8,
            descripcion="Pug de color negro, mide 50cm, mancha blanca en el pecho.",
            estado="ENCONTRADO", usuarioId=2,
        ),
        "min": 0.0,
        "max": 0.0,
    },
]


def _cumple(score: float, min_val: float, max_val: float) -> bool:
    return min_val <= score <= max_val


async def main() -> None:
    print("\n" + "=" * 60)
    print("  TEST — Motor de Coincidencias de Mascotas")
    print("=" * 60 + "\n")

    aprobados = 0
    for caso in CASOS:
        print(f"• {caso['nombre']}")
        resultado = await comparar(caso["perdida"], caso["candidata"])
        ok = _cumple(resultado.score, caso["min"], caso["max"])
        aprobados += ok
        icono = "✓" if ok else "✗"
        print(f"  {icono}  Score : {resultado.score:.4f}  ({resultado.porcentaje}%)")
        print(f"     Alerta : {'SÍ ⚠' if resultado.alerta else 'no'}")
        print(f"     Mensaje: {resultado.mensaje}")
        print(f"     Detalle: {resultado.detalle}")
        print()

    print(f"Resultado: {aprobados}/{len(CASOS)} casos aprobados.\n")


if __name__ == "__main__":
    asyncio.run(main())
