from fastapi import APIRouter, HTTPException

from app.api.deps import LLMServiceDep, RAGOptionalDep, SettingsDep
from app.models.schemas import GenerateRequest, GenerateResponse
from app.services.generate_service import generate_code

router = APIRouter(tags=["generate"])


@router.post("/generate", response_model=GenerateResponse)
async def generate(
    body: GenerateRequest,
    settings: SettingsDep,
    llm: LLMServiceDep,
    rag: RAGOptionalDep,
) -> GenerateResponse:
    if body.use_rag and rag is None:
        raise HTTPException(
            status_code=503,
            detail="RAG requires MongoDB; check MONGODB_URI and logs.",
        )
    text, rag_used, cache_hit = await generate_code(
        prompt=body.prompt,
        use_rag=body.use_rag,
        llm=llm,
        rag=rag,
        settings=settings,
    )
    return GenerateResponse(
        generated_code=text,
        rag_context_used=rag_used,
        cache_hit=cache_hit,
    )
