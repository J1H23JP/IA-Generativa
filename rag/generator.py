"""
Genera respuesta usando el LLM configurado.
- Si OLLAMA_MODEL está en .env  → usa Ollama (local, gratis)
- Si ANTHROPIC_API_KEY está     → usa Claude API
Soporta modo streaming (token a token) y modo normal.
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


def _build_messages(user_message: str) -> list[dict]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]


# ── Streaming ────────────────────────────────────────────────────────────────

def generate_stream(query: str, chunks: list[dict]):
    """Genera tokens uno a uno. Usar con StreamingResponse."""
    if not chunks:
        yield "No encontré información sobre este tema en las políticas internas disponibles."
        return

    context = build_context(chunks)
    user_message = f"CONTEXTO DE DOCUMENTOS:\n\n{context}\n\nPREGUNTA DEL EMPLEADO:\n{query}"

    if os.getenv("OLLAMA_MODEL"):
        from openai import OpenAI
        model = os.getenv("OLLAMA_MODEL", "llama3.2")
        client = OpenAI(
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
            api_key="ollama",
        )
        stream = client.chat.completions.create(
            model=model,
            messages=_build_messages(user_message),
            max_tokens=512,
            temperature=0.1,
            stream=True,
        )
        for chunk in stream:
            token = chunk.choices[0].delta.content
            if token:
                yield token

    elif os.getenv("ANTHROPIC_API_KEY"):
        import anthropic
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        with client.messages.stream(
            model="claude-sonnet-4-6",
            max_tokens=512,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        ) as stream:
            for text in stream.text_stream:
                yield text
    else:
        raise EnvironmentError(
            "No hay LLM configurado. Definí OLLAMA_MODEL o ANTHROPIC_API_KEY en el .env"
        )


# ── No-streaming (usado por demo_questions.py) ────────────────────────────────

def generate(query: str, chunks: list[dict]) -> dict:
    answer = "".join(generate_stream(query, chunks))
    model_name = f"ollama/{os.getenv('OLLAMA_MODEL','llama3.2')}" if os.getenv("OLLAMA_MODEL") else "claude-sonnet-4-6"
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
