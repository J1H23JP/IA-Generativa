"""
Gestión de ChromaDB como vector store persistente local.
"""
import os
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

COLLECTION_NAME = "politicas_internas"


def get_vectorstore(reset: bool = False) -> chromadb.Collection:
    chroma_path = os.getenv("CHROMA_PATH", "./vectorstore")
    client = chromadb.PersistentClient(
        path=chroma_path,
        settings=Settings(anonymized_telemetry=False),
    )

    if reset:
        try:
            client.delete_collection(COLLECTION_NAME)
            print(f"  Colección '{COLLECTION_NAME}' eliminada para reinicio.")
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
    return collection


def add_chunks(
    collection: chromadb.Collection,
    chunks: list[dict],
    embedder: SentenceTransformer,
    batch_size: int = 64,
):
    """Genera embeddings e inserta chunks en la colección."""
    from rag.embedder import embed_texts

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        texts = [c["text"] for c in batch]
        ids = [c["id"] for c in batch]
        metadatas = [
            {"source": c["source"], "page": c["page"], "chunk_index": c["chunk_index"]}
            for c in batch
        ]
        embeddings = embed_texts(texts, embedder)
        collection.add(ids=ids, documents=texts, embeddings=embeddings, metadatas=metadatas)


def count_chunks(collection: chromadb.Collection) -> int:
    return collection.count()
