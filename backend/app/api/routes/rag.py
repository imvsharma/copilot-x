from fastapi import APIRouter

from app.api.deps import RAGRequiredDep
from app.models.schemas import RAGIngestRequest, RAGIngestResponse

router = APIRouter(tags=["rag"])


@router.post("/rag/ingest", response_model=RAGIngestResponse)
async def rag_ingest(
    body: RAGIngestRequest,
    rag: RAGRequiredDep,
) -> RAGIngestResponse:
    doc_id = await rag.ingest(content=body.content, metadata=body.metadata)
    return RAGIngestResponse(document_id=doc_id)
