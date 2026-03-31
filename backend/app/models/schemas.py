"""Pydantic request/response models — API contract layer."""

from typing import Any

from pydantic import BaseModel, Field


# --- Generate ---
class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=32_000)
    use_rag: bool = Field(
        False,
        description="If true, retrieve top matching context chunks from MongoDB before calling the LLM.",
    )


class GenerateResponse(BaseModel):
    generated_code: str
    rag_context_used: bool = False
    cache_hit: bool = False


# --- Summarize ---
class SummarizeRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=256_000)


class SummarizeResponse(BaseModel):
    explanation: str
    cache_hit: bool = False


# --- RAG ingest ---
class RAGIngestRequest(BaseModel):
    """Store arbitrary text as retrievable context."""

    content: str = Field(..., min_length=1, max_length=256_000)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RAGIngestResponse(BaseModel):
    document_id: str


class HealthResponse(BaseModel):
    """Aggregate `status` reflects dependency checks; use HTTP 503 when not ok."""

    status: str = Field(
        ...,
        description='Overall: "ok" if dependencies are usable; "unhealthy" if any required check failed.',
    )
    mongodb: str = "unknown"
    redis: str = "unknown"
