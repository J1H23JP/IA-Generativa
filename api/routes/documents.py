import os
from fastapi import APIRouter, HTTPException
from api.models import DocumentsResponse, DocumentInfo, StatusResponse
from rag.vectorstore import get_vectorstore, count_chunks

router = APIRouter()


@router.get("/documents", response_model=DocumentsResponse)
async def list_documents():
    try:
        collection = get_vectorstore()
        total = count_chunks(collection)

        if total == 0:
            return DocumentsResponse(total_chunks=0, documents=[])

        # Obtener todos los metadatos para agrupar por fuente
        results = collection.get(include=["metadatas"])
        source_counts: dict[str, int] = {}
        for meta in results["metadatas"]:
            src = meta.get("source", "desconocido")
            source_counts[src] = source_counts.get(src, 0) + 1

        documents = [
            DocumentInfo(name=name, chunks=count)
            for name, count in sorted(source_counts.items())
        ]
        return DocumentsResponse(total_chunks=total, documents=documents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=StatusResponse)
async def status():
    try:
        collection = get_vectorstore()
        total = count_chunks(collection)
        return StatusResponse(
            status="ok" if total > 0 else "sin_documentos",
            total_chunks=total,
            embedding_model=os.getenv("EMBEDDING_MODEL", "paraphrase-multilingual-mpnet-base-v2"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
