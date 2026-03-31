from fastapi import APIRouter

from app.api.deps import LLMServiceDep
from app.models.schemas import SummarizeRequest, SummarizeResponse
from app.services.summarize_service import summarize_code

router = APIRouter(tags=["summarize"])


@router.post("/summarize", response_model=SummarizeResponse)
async def summarize(
    body: SummarizeRequest,
    llm: LLMServiceDep,
) -> SummarizeResponse:
    explanation, cache_hit = await summarize_code(code=body.code, llm=llm)
    return SummarizeResponse(explanation=explanation, cache_hit=cache_hit)
