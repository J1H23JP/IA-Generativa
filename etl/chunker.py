import uuid
from langchain_text_splitters import RecursiveCharacterTextSplitter


def chunk_pages(pages: list[dict], chunk_size: int = 500, chunk_overlap: int = 50) -> list[dict]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
    )
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
