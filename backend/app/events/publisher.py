"""
Domain event publisher — placeholder for Kafka / Redis Streams / SNS.

Handlers must stay side-effect free with respect to core business rules: publishing
failures should not break user requests (log and continue).
"""

from typing import Any, Protocol, runtime_checkable

from app.core.logging import get_logger

logger = get_logger(__name__)


@runtime_checkable
class EventPublisher(Protocol):
    async def publish(self, topic: str, payload: dict[str, Any]) -> None: ...


class NoOpEventPublisher:
    """Default: no outbound events (local dev, tests)."""

    async def publish(self, topic: str, payload: dict[str, Any]) -> None:
        logger.debug("event noop topic=%s keys=%s", topic, list(payload.keys()))


class LoggingEventPublisher:
    """Structured log sink until a real broker is wired (easy to grep in aggregators)."""

    async def publish(self, topic: str, payload: dict[str, Any]) -> None:
        logger.info("event topic=%s payload=%s", topic, payload)


class RedisStreamPublisher:
    """
    Stub for Redis Streams (XADD). Implement when infra provides a stream name and ACL.

    Keeps constructor signature explicit so swapping to Kafka only changes this class.
    """

    def __init__(self, _redis: Any, _stream: str = "copilotx:events") -> None:
        self._redis = _redis
        self._stream = _stream

    async def publish(self, topic: str, payload: dict[str, Any]) -> None:
        if self._redis is None:
            await NoOpEventPublisher().publish(topic, payload)
            return
        # Future: await self._redis.xadd(self._stream, {"topic": topic, "body": json.dumps(payload)})
        logger.debug("redis stream publish stub topic=%s", topic)
