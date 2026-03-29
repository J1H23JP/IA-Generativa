import os
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File
from api.models import DocumentsResponse, DocumentInfo, StatusResponse
from rag.vectorstore import get_vectorstore, count_chunks, delete_chunks_by_source

router = APIRouter()

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}


@router.get("/documents", response_model=DocumentsResponse)
async def list_documents():
    try:
        collection = get_vectorstore()
        total = count_chunks(collection)
        if total == 0:
            return DocumentsResponse(total_chunks=0, documents=[])

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


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Sube un archivo PDF, DOCX o TXT, lo guarda en docs/ y lo indexa automáticamente.
    """
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Formato no soportado: {ext}. Permitidos: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    docs_dir = os.getenv("DOCS_PATH", "./docs")
    os.makedirs(docs_dir, exist_ok=True)
    save_path = os.path.join(docs_dir, file.filename)

    # Guardar archivo
    content = await file.read()
    with open(save_path, "wb") as f:
        f.write(content)

    # Indexar
    try:
        from etl.ingest import ingest_file
        chunks_added = ingest_file(save_path)
    except Exception as e:
        os.remove(save_path)
        raise HTTPException(status_code=500, detail=f"Error al indexar: {str(e)}")

    return {
        "filename": file.filename,
        "chunks_added": chunks_added,
        "message": f"'{file.filename}' indexado correctamente con {chunks_added} fragmentos."
    }


@router.delete("/documents/{filename}")
async def delete_document(filename: str):
    """
    Elimina un documento indexado: borra el archivo de docs/ (si existe) y sus chunks del vectorstore.
    """
    docs_dir = os.getenv("DOCS_PATH", "./docs")
    file_path = os.path.join(docs_dir, filename)

    # Eliminar chunks del vectorstore siempre
    try:
        collection = get_vectorstore()
        chunks_deleted = delete_chunks_by_source(collection, filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar chunks: {str(e)}")

    # Eliminar archivo físico si existe
    file_deleted = False
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            file_deleted = True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al eliminar archivo: {str(e)}")

    message = f"'{filename}' eliminado del índice. {chunks_deleted} fragmentos removidos."
    if file_deleted:
        message += " Archivo físico eliminado."
    else:
        message += " (Archivo físico no encontrado, pero chunks eliminados.)"

    return {
        "filename": filename,
        "chunks_deleted": chunks_deleted,
        "file_deleted": file_deleted,
        "message": message
    }
