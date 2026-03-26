"""
Divide el texto de cada página en chunks con overlap.
Usa LangChain RecursiveCharacterTextSplitter para respetar estructura de párrafos.
"""
import os
import uuid
from langchain_text_splitters import RecursiveCharacterTextSplitter


def build_splitter(chunk_size: int = 500, chunk_overlap: int = 50) -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
    )


def chunk_pages(pages: list[dict], chunk_size: int = 500, chunk_overlap: int = 50) -> list[dict]:
    """
    Recibe lista de páginas limpias y retorna lista de chunks con metadata.
    Cada chunk: {id, text, source, page, chunk_index}
    """
    splitter = build_splitter(chunk_size, chunk_overlap)
    chunks = []

    for page in pages:
        parts = splitter.split_text(page["text"])
        for i, part in enumerate(parts):
            if part.strip():
                chunks.append({
                    "id": str(uuid.uuid4()),
                    "text": part.strip(),
                    "source": page["source"],
                    "page": page["page"],
                    "chunk_index": i,
                })

    return chunks
