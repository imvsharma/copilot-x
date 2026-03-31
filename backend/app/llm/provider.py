"""
OpenAI transport — HTTP + response validation + Redis cache only.

No business rules or templates here; `LLMService` sits above this for orchestration.
Swapping providers (Anthropic, Azure OpenAI) means replacing this module while keeping
`LLMService` and routes unchanged.
"""

import hashlib
import json
from typing import Any

from openai import AsyncOpenAI

from app.core.config import Settings
from app.core.exceptions import ConfigurationError, ExternalServiceError
from app.core.logging import get_logger

logger = get_logger(__name__)


class OpenAIProvider:
    """Thin async wrapper around OpenAI chat + embeddings with optional Redis caching."""

    def __init__(self, settings: Settings, redis: Any | None) -> None:
        key = settings.openai_api_key.get_secret_value()
        if not key:
            raise ConfigurationError("OPENAI_API_KEY is not set")
        self._client = AsyncOpenAI(api_key=key)
        self._settings = settings
        self._redis = redis

    async def chat_completion(
        self,
        *,
        messages: list[dict[str, str]],
        temperature: float,
        use_cache: bool,
    ) -> tuple[str, bool]:
        """
        Returns (assistant text, cache_hit).

        Caches on identical (messages, temperature) to dedupe spend.
        """
        cache_key = self._cache_key(messages, temperature)
        if use_cache and self._settings.cache_enabled and self._redis:
            try:
                cached = await self._redis.get(cache_key)
                if cached:
                    return cached.decode("utf-8"), True
            except Exception as e:
                logger.warning("Redis get failed (continuing without cache): %s", e)

        try:
            resp = await self._client.chat.completions.create(
                model=self._settings.openai_model,
                messages=messages,
                temperature=temperature,
            )
            if not resp.choices:
                raise ExternalServiceError("LLM returned no choices")
            msg = resp.choices[0].message
            if msg is None:
                raise ExternalServiceError("LLM returned no message")
            text = (msg.content or "").strip()
        except ExternalServiceError:
            raise
        except Exception as e:
            logger.exception("OpenAI chat completion failed")
            raise ExternalServiceError("LLM request failed") from e

        if use_cache and self._settings.cache_enabled and self._redis and text:
            try:
                await self._redis.setex(
                    cache_key,
                    self._settings.cache_ttl_seconds,
                    text.encode("utf-8"),
                )
            except Exception as e:
                logger.warning("Redis set failed: %s", e)

        return text, False

    async def embed_text(self, text: str) -> list[float]:
        try:
            resp = await self._client.embeddings.create(
                model=self._settings.openai_embedding_model,
                input=text[:8000],
            )
            if not resp.data:
                raise ExternalServiceError("Embedding API returned no vectors")
            row = resp.data[0]
            if row.embedding is None:
                raise ExternalServiceError("Embedding vector missing")
            return list(row.embedding)
        except ExternalServiceError:
            raise
        except Exception as e:
            logger.exception("OpenAI embedding failed")
            raise ExternalServiceError("Embedding request failed") from e

    @staticmethod
    def _cache_key(messages: list[dict[str, str]], temperature: float) -> str:
        payload = json.dumps({"m": messages, "t": temperature}, sort_keys=True)
        digest = hashlib.sha256(payload.encode()).hexdigest()
        return f"llm:chat:{digest}"
