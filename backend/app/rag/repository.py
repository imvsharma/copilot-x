"""MongoDB persistence for RAG chunks — Motor async API."""

from datetime import datetime, timezone
from typing import Any

from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase

COLLECTION = "context_chunks"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ContextRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._col: AsyncIOMotorCollection = db[COLLECTION]

    async def ensure_indexes(self) -> None:
        # Single-field index for metadata filters; embedding search is in-app for MVP
        await self._col.create_index([("created_at", -1)])

    async def insert_chunk(
        self,
        *,
        content: str,
        embedding: list[float],
        metadata: dict[str, Any],
    ) -> str:
        doc = {
            "content": content,
            "embedding": embedding,
            "metadata": metadata,
            "created_at": _utcnow(),
        }
        res = await self._col.insert_one(doc)
        return str(res.inserted_id)

    async def fetch_all_with_embeddings(self) -> list[dict[str, Any]]:
        cursor = self._col.find({"embedding": {"$exists": True, "$ne": []}})
        return await cursor.to_list(length=None)
