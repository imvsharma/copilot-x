"""Use case: code generation with optional RAG (orchestration only — no HTTP, no SDK)."""

from app.core.config import Settings
from app.core.exceptions import ExternalServiceError
from app.llm import system_prompts
from app.llm.service import LLMService
from app.prompts.loader import PromptName, render
from app.rag.service import RAGService


async def generate_code(
    *,
    prompt: str,
    use_rag: bool,
    llm: LLMService,
    rag: RAGService | None,
    settings: Settings,
) -> tuple[str, bool, bool]:
    """
    Returns (generated_text, rag_context_used, cache_hit).
    """
    rag_block = ""
    rag_used = False
    if use_rag and rag is not None:
        rag_block, rag_used = await rag.retrieve_context_block(prompt)

    display_ctx = rag_block if rag_block else "(no retrieved context)"
    user_content = render(
        PromptName.api_generation,
        user_prompt=prompt,
        context=display_ctx,
    )
    text, cache_hit = await llm.chat(
        user_content=user_content,
        system_prompt=system_prompts.CODE_GENERATION,
        temperature=0.2,
        use_cache=True,
    )
    if not text:
        raise ExternalServiceError("Empty LLM response")
    return text, rag_used, cache_hit
