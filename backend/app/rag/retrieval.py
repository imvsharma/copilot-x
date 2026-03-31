"""Lightweight vector similarity over stored embeddings (MVP-scale)."""

import math
from typing import Any

from app.core.config import Settings


def _cosine(a: list[float], b: list[float]) -> float:
    if len(a) != len(b) or not a:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def retrieve_top_k(
    *,
    query_embedding: list[float],
    documents: list[dict[str, Any]],
    settings: Settings,
) -> list[str]:
    """
    Returns up to `rag_top_k` chunk texts sorted by cosine similarity,
    filtered by `rag_min_similarity`.
    """
    scored: list[tuple[float, str]] = []
    for doc in documents:
        emb = doc.get("embedding")
        content = doc.get("content")
        if not isinstance(emb, list) or not content:
            continue
        sim = _cosine(query_embedding, [float(x) for x in emb])
        if sim >= settings.rag_min_similarity:
            scored.append((sim, str(content)))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[: settings.rag_top_k]
    return [t for _, t in top]


def format_rag_block(chunks: list[str]) -> str:
    if not chunks:
        return ""
    parts = [f"[Context {i + 1}]\n{c}" for i, c in enumerate(chunks)]
    return "\n\n".join(parts)
