"""
FastAPI dependencies — composition root for the modular monolith.

`LLMService` / `RAGService` are the stable seams for a future split: same interfaces
can be backed by in-process implementations (here) or remote clients (later).
"""

from typing import Annotated, Any

from fastapi import Depends, HTTPException, Request

from app.core.config import Settings, get_settings
from app.llm.service import LLMService
from app.rag.repository import ContextRepository
from app.rag.service import RAGService


def get_redis(request: Request) -> Any | None:
    return getattr(request.app.state, "redis", None)


def get_mongo_db_optional(request: Request):
    return getattr(request.app.state, "mongo_db", None)


def get_llm_service(request: Request) -> LLMService:
    svc = getattr(request.app.state, "llm_service", None)
    if svc is None:
        raise HTTPException(
            status_code=503,
            detail="LLM is not configured (set OPENAI_API_KEY).",
        )
    return svc


def get_rag_service_optional(
    request: Request,
    llm: Annotated[LLMService, Depends(get_llm_service)],
) -> RAGService | None:
    db = get_mongo_db_optional(request)
    if db is None:
        return None
    settings = get_settings()
    return RAGService(ContextRepository(db), settings, llm)


def get_rag_service_required(
    request: Request,
    llm: Annotated[LLMService, Depends(get_llm_service)],
) -> RAGService:
    db = get_mongo_db_optional(request)
    if db is None:
        raise HTTPException(status_code=503, detail="MongoDB unavailable")
    settings = get_settings()
    return RAGService(ContextRepository(db), settings, llm)


SettingsDep = Annotated[Settings, Depends(get_settings)]
LLMServiceDep = Annotated[LLMService, Depends(get_llm_service)]
RAGOptionalDep = Annotated[RAGService | None, Depends(get_rag_service_optional)]
RAGRequiredDep = Annotated[RAGService, Depends(get_rag_service_required)]
RedisDep = Annotated[Any | None, Depends(get_redis)]
