"""Use case: summarize code via prompt template + LLM."""

from app.core.exceptions import ExternalServiceError
from app.llm import system_prompts
from app.llm.service import LLMService
from app.prompts.loader import PromptName, render


async def summarize_code(*, code: str, llm: LLMService) -> tuple[str, bool]:
    """Returns (explanation, cache_hit)."""
    user_content = render(PromptName.summarization, code=code)
    text, cache_hit = await llm.chat(
        user_content=user_content,
        system_prompt=system_prompts.CODE_SUMMARIZATION,
        temperature=0.3,
        use_cache=True,
    )
    if not text:
        raise ExternalServiceError("Empty LLM response")
    return text, cache_hit
