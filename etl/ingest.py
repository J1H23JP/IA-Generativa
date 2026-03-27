"""
Orquestador del pipeline ETL completo.
Uso: python -m etl.ingest  (o desde scripts/run_etl.py)
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

from etl.extractor import extract_all
from etl.cleaner import clean_pages
from etl.chunker import chunk_pages
from rag.embedder import get_embedder
from rag.vectorstore import get_vectorstore, add_chunks


def run_etl(docs_dir: str = None, reset: bool = False):
    docs_dir = docs_dir or os.getenv("DOCS_PATH", "./docs")
    chunk_size = int(os.getenv("CHUNK_SIZE", 500))
    chunk_overlap = int(os.getenv("CHUNK_OVERLAP", 50))

    print("=" * 50)
    print("PIPELINE ETL — Buscador de Políticas Internas")
    print("=" * 50)

    # 1. Extracción
    print("\n[1/4] Extrayendo texto de documentos...")
    pages = extract_all(docs_dir)
    print(f"      {len(pages)} páginas extraídas")

    # 2. Limpieza
    print("\n[2/4] Limpiando y normalizando texto...")
    pages = clean_pages(pages)
    print(f"      {len(pages)} páginas luego de limpieza")

    # 3. Chunking
    print("\n[3/4] Dividiendo en chunks...")
    chunks = chunk_pages(pages, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    print(f"      {len(chunks)} chunks generados")
    for src in set(c["source"] for c in chunks):
        n = sum(1 for c in chunks if c["source"] == src)
        print(f"        - {src}: {n} chunks")

    # 4. Embeddings + almacenamiento
    print("\n[4/4] Generando embeddings y guardando en ChromaDB...")
    embedder = get_embedder()
    vectorstore = get_vectorstore(reset=reset)
    add_chunks(vectorstore, chunks, embedder)
    print(f"      {len(chunks)} chunks almacenados exitosamente")

    print("\n✓ ETL completado. El buscador está listo para consultas.")
    print("=" * 50)
    return len(chunks)


def ingest_file(file_path: str) -> int:
    """Indexa un único archivo nuevo sin re-procesar los existentes."""
    chunk_size = int(os.getenv("CHUNK_SIZE", 500))
    chunk_overlap = int(os.getenv("CHUNK_OVERLAP", 50))

    from etl.extractor import extract
    from etl.cleaner import clean_pages
    from etl.chunker import chunk_pages
    from rag.embedder import get_embedder
    from rag.vectorstore import get_vectorstore, add_chunks

    pages = extract(file_path)
    pages = clean_pages(pages)
    chunks = chunk_pages(pages, chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    embedder = get_embedder()
    vectorstore = get_vectorstore()
    add_chunks(vectorstore, chunks, embedder)
    return len(chunks)


if __name__ == "__main__":
    reset = "--reset" in sys.argv
    run_etl(reset=reset)
