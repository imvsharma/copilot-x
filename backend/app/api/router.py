"""Aggregates versioned HTTP routes — single place to mount `API_PREFIX` for gateways."""

from fastapi import APIRouter

from app.api.routes import generate, health, rag, summarize


def build_api_router() -> APIRouter:
    router = APIRouter()
    router.include_router(generate.router)
    router.include_router(summarize.router)
    router.include_router(rag.router)
    router.include_router(health.router)
    return router
