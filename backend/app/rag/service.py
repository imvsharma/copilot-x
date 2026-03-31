"""
RAG application service — orchestrates storage, embeddings, and retrieval.

Vector math stays in `retrieval.py` (pure functions). Repository is persistence only.
A future dedicated "RAG service" would expose this class over the network; Mongo could
be replaced by a vector DB without changing callers if chunk/embedding contracts hold.
"""

from typing import Any

from app.core.config import Settings
from app.llm.service import LLMService
from app.rag.repository import ContextRepository
from app.rag.retrieval import format_rag_block, retrieve_top_k


class RAGService:
    def __init__(
        self,
        repo: ContextRepository,
        settings: Settings,
        llm: LLMService,
    ) -> None:
        self._repo = repo
        self._settings = settings
        self._llm = llm

    async def retrieve_context_block(self, prompt: str) -> tuple[str, bool]:
        """
        Embed the query, score stored chunks, return formatted block for the LLM.

        Returns (block_text, rag_used) where rag_used is True if any chunk passed the
        similarity threshold.
        """
        q_emb = await self._llm.embed(prompt)
        docs = await self._repo.fetch_all_with_embeddings()
        chunks = retrieve_top_k(
            query_embedding=q_emb,
            documents=docs,
            settings=self._settings,
        )
        block = format_rag_block(chunks)
        return block, bool(chunks)

    async def ingest(
        self,
        *,
        content: str,
        metadata: dict[str, Any],
    ) -> str:
        emb = await self._llm.embed(content)
        return await self._repo.insert_chunk(
            content=content,
            embedding=emb,
            metadata=metadata,
        )
