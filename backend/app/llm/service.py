"""
LLM application service — single entry for chat + embeddings used by use cases.

Routes and HTTP adapters depend on this class, not on `OpenAIProvider`, so the API
layer stays decoupled from vendor SDKs. Domain events are emitted here for future
Kafka/Redis Streams consumers without coupling business logic to transport.
"""

from typing import Any

from app.core.config import Settings
from app.core.logging import get_logger
from app.events.publisher import EventPublisher, NoOpEventPublisher
from app.llm.provider import OpenAIProvider

logger = get_logger(__name__)


class LLMService:
    """
    Facade over `OpenAIProvider` with stable method names for the service layer.

    When splitting into an "LLM microservice", this interface maps cleanly to a gRPC
    or HTTP client; `OpenAIProvider` stays server-side in that service only.
    """

    def __init__(
        self,
        settings: Settings,
        redis: Any | None,
        events: EventPublisher | None = None,
    ) -> None:
        self._settings = settings
        self._provider = OpenAIProvider(settings, redis)
        self._events = events or NoOpEventPublisher()

    async def chat(
        self,
        *,
        user_content: str,
        system_prompt: str,
        temperature: float = 0.2,
        use_cache: bool = True,
    ) -> tuple[str, bool]:
        """Returns (text, cache_hit). Emits a lightweight event on non-cached completions."""
        messages: list[dict[str, str]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]
        text, cache_hit = await self._provider.chat_completion(
            messages=messages,
            temperature=temperature,
            use_cache=use_cache,
        )
        if not cache_hit:
            await self._events.publish(
                "copilotx.llm.chat.completed",
                {
                    "model": self._settings.openai_model,
                    "cached": False,
                },
            )
        return text, cache_hit

    async def embed(self, text: str) -> list[float]:
        # Intentionally no domain event per embed: RAG paths call this frequently;
        # emit metrics at the RAG service or via sampling if needed.
        return await self._provider.embed_text(text)
