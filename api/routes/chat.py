import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from api.models import ChatRequest
from rag.retriever import retrieve
from rag.generator import generate_stream

router = APIRouter()


@router.post("/chat")
async def chat(request: ChatRequest):
    """
    Endpoint de chat con streaming (Server-Sent Events).
    Primero envía metadata (fuentes, chunks), luego tokens de la respuesta.
    """
    try:
        chunks = retrieve(query=request.question, top_k=request.top_k)
        sources = list({c["source"] for c in chunks})
        chunks_meta = [
            {"source": c["source"], "page": c["page"], "score": c["score"], "text": c["text"][:200]}
            for c in chunks
        ]

        def event_stream():
            # 1. Primero mandamos los metadatos (fuentes y chunks recuperados)
            meta = {"type": "meta", "sources": sources, "chunks": chunks_meta, "chunks_used": len(chunks)}
            yield f"data: {json.dumps(meta, ensure_ascii=False)}\n\n"

            # 2. Luego los tokens de la respuesta
            try:
                for token in generate_stream(request.question, chunks):
                    payload = {"type": "token", "token": token}
                    yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
            except Exception as e:
                error = {"type": "error", "message": str(e)}
                yield f"data: {json.dumps(error)}\n\n"

            yield "data: [DONE]\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
