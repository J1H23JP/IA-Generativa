"""
Genera respuesta usando el LLM configurado.
- Si OLLAMA_MODEL está en .env  → usa Ollama (local, gratis)
- Si ANTHROPIC_API_KEY está     → usa Claude API
"""
import os

SYSTEM_PROMPT = """Eres un asistente experto en políticas internas de la empresa.
Tu función es responder preguntas de los empleados basándote ÚNICAMENTE en los documentos oficiales que se te proporcionan como contexto.

REGLAS:
1. Solo responde con información presente en el contexto proporcionado.
2. Si la información no está en los documentos, responde exactamente: "No encontré información sobre este tema en las políticas internas disponibles."
3. Cita siempre la fuente entre paréntesis al final de cada afirmación relevante, por ejemplo: (Fuente: politica_vacaciones.txt).
4. Sé claro, conciso y usa lenguaje accesible para empleados.
5. Si hay múltiples políticas relevantes, menciónalas todas.
6. No inventes, no asumas, no extrapoles más allá del contexto."""


def build_context(chunks: list[dict]) -> str:
    parts = []
    for i, chunk in enumerate(chunks, 1):
        parts.append(
            f"[Fragmento {i} — Fuente: {chunk['source']}, Página: {chunk['page']}]\n{chunk['text']}"
        )
    return "\n\n---\n\n".join(parts)


def _generate_ollama(user_message: str) -> tuple[str, str]:
    """Llama a Ollama vía su API compatible con OpenAI."""
    from openai import OpenAI

    model = os.getenv("OLLAMA_MODEL", "llama3.2")
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")

    client = OpenAI(base_url=base_url, api_key="ollama")
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        max_tokens=1024,
        temperature=0.1,
    )
    return response.choices[0].message.content, f"ollama/{model}"


def _generate_claude(user_message: str) -> tuple[str, str]:
    """Llama a Claude via Anthropic API."""
    import anthropic

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )
    return response.content[0].text, response.model


def generate(query: str, chunks: list[dict]) -> dict:
    """
    Genera respuesta RAG con el LLM configurado.
    Retorna: {answer, sources, model, chunks_used, chunks}
    """
    if not chunks:
        return {
            "answer": "No encontré información sobre este tema en las políticas internas disponibles.",
            "sources": [],
            "model": "N/A",
            "chunks_used": 0,
            "chunks": [],
        }

    context = build_context(chunks)
    user_message = f"CONTEXTO DE DOCUMENTOS:\n\n{context}\n\nPREGUNTA DEL EMPLEADO:\n{query}"

    # Selección automática de backend
    if os.getenv("OLLAMA_MODEL"):
        answer, model_name = _generate_ollama(user_message)
    elif os.getenv("ANTHROPIC_API_KEY"):
        answer, model_name = _generate_claude(user_message)
    else:
        raise EnvironmentError(
            "No hay LLM configurado. Definí OLLAMA_MODEL o ANTHROPIC_API_KEY en el .env"
        )

    return {
        "answer": answer,
        "sources": list({c["source"] for c in chunks}),
        "model": model_name,
        "chunks_used": len(chunks),
        "chunks": [
            {"source": c["source"], "page": c["page"], "score": c["score"], "text": c["text"][:200]}
            for c in chunks
        ],
    }
