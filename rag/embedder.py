"""
Genera embeddings usando sentence-transformers (local, sin costo de API).
Modelo multilingüe para soporte en español.
"""
import os
from sentence_transformers import SentenceTransformer

_embedder_instance = None


def get_embedder() -> SentenceTransformer:
    global _embedder_instance
    if _embedder_instance is None:
        model_name = os.getenv("EMBEDDING_MODEL", "paraphrase-multilingual-mpnet-base-v2")
        print(f"  Cargando modelo de embeddings: {model_name}")
        _embedder_instance = SentenceTransformer(model_name)
    return _embedder_instance


def embed_texts(texts: list[str], embedder: SentenceTransformer = None) -> list[list[float]]:
    if embedder is None:
        embedder = get_embedder()
    vectors = embedder.encode(texts, show_progress_bar=False, normalize_embeddings=True)
    return vectors.tolist()
