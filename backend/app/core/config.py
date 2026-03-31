"""
Application settings loaded from environment.

Service boundaries (future microservices): each worker reads the same env contract;
splitting later means moving Mongo/Redis URLs to service-specific prefixes without
changing domain logic.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "CopilotX API"
    debug: bool = False
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    # `json` enables one-line JSON logs for Loki/Datadog; `text` is human-readable locally
    log_format: Literal["text", "json"] = "text"

    # Mount all API routers under this prefix (e.g. /api/v1) when sitting behind a gateway
    api_prefix: str = ""

    # Domain events: noop | log (stdout) — future: wire Redis Streams / Kafka in main.py
    event_sink: Literal["noop", "log"] = "noop"

    # OpenAI — never log the raw key (SecretStr hides repr)
    openai_api_key: SecretStr = Field(default=SecretStr(""), description="OpenAI API key")
    openai_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"

    # MongoDB (Motor async driver)
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db: str = "copilotx"

    # Redis — LLM response cache
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl_seconds: int = 3600
    cache_enabled: bool = True

    # RAG retrieval
    rag_top_k: int = 3
    rag_min_similarity: float = 0.25


@lru_cache
def get_settings() -> Settings:
    return Settings()
