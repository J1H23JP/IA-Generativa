"""
Script de demo: lanza una serie de preguntas de ejemplo y muestra las respuestas.
Útil para mostrar el sistema en acción sin abrir el navegador.

Uso:
  python scripts/demo_questions.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from rag.retriever import retrieve
from rag.generator import generate

DEMO_QUESTIONS = [
    "¿Cuántos días de vacaciones me corresponden si llevo 3 años en la empresa?",
    "¿Cuántos días de home office puedo tomar por semana sin aprobación previa?",
    "¿Qué hago si pierdo o me roban la laptop de la empresa?",
    "¿Puedo usar ChatGPT para mi trabajo diario?",
    "¿Cuál es el límite de gasto diario en alimentación cuando viajo por negocio?",
]


def run_demo():
    print("=" * 60)
    print("DEMO — Buscador Inteligente de Políticas Internas")
    print("=" * 60)

    for i, question in enumerate(DEMO_QUESTIONS, 1):
        print(f"\n[Pregunta {i}/{len(DEMO_QUESTIONS)}]")
        print(f"Q: {question}")
        print("-" * 40)

        chunks = retrieve(query=question, top_k=5)
        result = generate(query=question, chunks=chunks)

        print(f"A: {result['answer']}")
        print(f"\nFuentes: {', '.join(result['sources'])}")
        print(f"Chunks usados: {result['chunks_used']} | Modelo: {result['model']}")

        if i < len(DEMO_QUESTIONS):
            input("\nPresioná Enter para la siguiente pregunta...")

    print("\n" + "=" * 60)
    print("Demo finalizado.")


if __name__ == "__main__":
    run_demo()
