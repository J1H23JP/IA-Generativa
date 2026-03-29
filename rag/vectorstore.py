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
        except Exception:
            pass
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def add_chunks(collection, chunks: list[dict], embedder: SentenceTransformer, batch_size: int = 64):
    from rag.embedder import embed_texts
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i: i + batch_size]
        collection.add(
            ids=[c["id"] for c in batch],
            documents=[c["text"] for c in batch],
            embeddings=embed_texts([c["text"] for c in batch], embedder),
            metadatas=[{"source": c["source"], "page": c["page"], "chunk_index": c["chunk_index"]} for c in batch],
        )


def count_chunks(collection) -> int:
    return collection.count()


def delete_chunks_by_source(collection, source: str) -> int:
    """Delete all chunks from the collection that have the given source in metadata."""
    try:
        # Get all ids where metadata source matches
        results = collection.get(include=["metadatas"])
        ids_to_delete = [
            results["ids"][i] for i, meta in enumerate(results["metadatas"])
            if meta.get("source") == source
        ]
        if ids_to_delete:
            collection.delete(ids=ids_to_delete)
        return len(ids_to_delete)
    except Exception as e:
        raise Exception(f"Error deleting chunks for source {source}: {str(e)}")
