"""
Búsqueda semántica: dado un query, retorna los top-k chunks más relevantes.
"""
import os
import chromadb
from sentence_transformers import SentenceTransformer
from rag.embedder import embed_texts, get_embedder
from rag.vectorstore import get_vectorstore


def retrieve(
    query: str,
    top_k: int = None,
    collection: chromadb.Collection = None,
    embedder: SentenceTransformer = None,
) -> list[dict]:
    """
    Retorna lista de chunks relevantes con su score de similitud.
    Cada item: {text, source, page, chunk_index, score}
    """
    top_k = top_k or int(os.getenv("TOP_K_RESULTS", 5))
    if collection is None:
        collection = get_vectorstore()
    if embedder is None:
        embedder = get_embedder()

    query_embedding = embed_texts([query], embedder)[0]

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        # ChromaDB con cosine devuelve distancia (0=idéntico, 2=opuesto)
        # Convertimos a score de similitud: 1 - dist/2
        score = round(1 - dist / 2, 4)
        chunks.append({
            "text": doc,
            "source": meta.get("source", "desconocido"),
            "page": meta.get("page", 1),
            "chunk_index": meta.get("chunk_index", 0),
            "score": score,
        })

    # Ordenar por score descendente
    chunks.sort(key=lambda x: x["score"], reverse=True)
    return chunks
