from fastapi import APIRouter, HTTPException
from api.models import ChatRequest, ChatResponse, ChunkInfo
from rag.retriever import retrieve
from rag.generator import generate

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        chunks = retrieve(query=request.question, top_k=request.top_k)
        result = generate(query=request.question, chunks=chunks)
        return ChatResponse(
            answer=result["answer"],
            sources=result["sources"],
            model=result["model"],
            chunks_used=result["chunks_used"],
            chunks=[ChunkInfo(**c) for c in result.get("chunks", [])],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
