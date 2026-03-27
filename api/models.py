from pydantic import BaseModel, Field
from typing import Optional


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=1000)
    top_k: Optional[int] = Field(default=5, ge=1, le=10)


class ChunkInfo(BaseModel):
    source: str
    page: int
    score: float
    text: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]
    model: str
    chunks_used: int
    chunks: list[ChunkInfo]


class DocumentInfo(BaseModel):
    name: str
    chunks: int


class DocumentsResponse(BaseModel):
    total_chunks: int
    documents: list[DocumentInfo]


class StatusResponse(BaseModel):
    status: str
    total_chunks: int
    embedding_model: str
