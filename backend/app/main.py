"""
CopilotX FastAPI application — modular monolith entrypoint.

Layers:
- `app.api`: HTTP adapters (routers, DI only)
- `app.services`: application use cases
- `app.llm`: LLMService + OpenAI provider (vendor boundary)
- `app.rag`: RAGService + repository + pure retrieval math
- `app.prompts`: prompt assets
- `app.events`: domain event publisher (future broker)
- `app.core`: config, logging

Future extraction: deploy `LLMService` and `RAGService` as separate processes; replace
`deps.py` with clients and keep `app.services` unchanged.
"""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient
from redis.asyncio import Redis

from app.api.router import build_api_router
from app.core.config import get_settings
from app.core.exceptions import CopilotXError, ConfigurationError, ExternalServiceError
from app.core.logging import get_logger, setup_logging
from app.events.publisher import LoggingEventPublisher, NoOpEventPublisher
from app.llm.service import LLMService
from app.rag.repository import ContextRepository

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    setup_logging(settings.log_level, settings.log_format)

    app.state.mongo_client = None
    app.state.mongo_db = None
    app.state.redis = None
    app.state.llm_service = None

    # MongoDB
    try:
        app.state.mongo_client = AsyncIOMotorClient(
            settings.mongodb_uri,
            serverSelectionTimeoutMS=5000,
        )
        app.state.mongo_db = app.state.mongo_client[settings.mongodb_db]
        repo = ContextRepository(app.state.mongo_db)
        await repo.ensure_indexes()
        logger.info("MongoDB connected: db=%s", settings.mongodb_db)
    except Exception as e:
        logger.exception("MongoDB connection failed: %s", e)
        if app.state.mongo_client:
            app.state.mongo_client.close()
        app.state.mongo_client = None
        app.state.mongo_db = None

    # Redis (optional for cache)
    try:
        app.state.redis = Redis.from_url(settings.redis_url, decode_responses=False)
        await app.state.redis.ping()
        logger.info("Redis connected")
    except Exception as e:
        logger.warning("Redis unavailable (LLM cache disabled): %s", e)
        app.state.redis = None

    # Event sink (placeholder for Kafka / Redis Streams)
    if settings.event_sink == "log":
        publisher: LoggingEventPublisher | NoOpEventPublisher = LoggingEventPublisher()
    else:
        publisher = NoOpEventPublisher()

    # LLM service (requires API key)
    if settings.openai_api_key.get_secret_value():
        try:
            app.state.llm_service = LLMService(settings, app.state.redis, publisher)
            logger.info("LLM service ready (model=%s)", settings.openai_model)
        except ConfigurationError as e:
            logger.warning("LLM not configured: %s", e.message)
    else:
        logger.warning("OPENAI_API_KEY not set — /generate, /summarize, /rag/ingest will return 503")

    yield

    if app.state.redis:
        await app.state.redis.aclose()
    if app.state.mongo_client:
        app.state.mongo_client.close()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    api = build_api_router()
    app.include_router(api, prefix=settings.api_prefix)

    @app.exception_handler(CopilotXError)
    async def copilotx_handler(_: Request, exc: CopilotXError) -> JSONResponse:
        if isinstance(exc, (ConfigurationError, ExternalServiceError)):
            status = 503
        else:
            status = 400
        return JSONResponse(
            status_code=status,
            content={"detail": exc.message, "code": exc.code},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={"detail": exc.errors(), "code": "validation_error"},
        )

    return app


app = create_app()
