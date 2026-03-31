"""
Loads reusable prompt templates from disk.

Templates are plain text with optional `{placeholder}` slots — keeps prompts versioned
and reviewable without code changes.
"""

from enum import Enum
from functools import lru_cache
from pathlib import Path

from app.core.exceptions import ConfigurationError


class PromptName(str, Enum):
    api_generation = "api_generation"
    summarization = "summarization"
    documentation = "documentation"


_TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"


@lru_cache
def get_template(name: PromptName) -> str:
    path = _TEMPLATES_DIR / f"{name.value}.txt"
    if not path.is_file():
        raise ConfigurationError(f"Missing prompt template: {path}")
    return path.read_text(encoding="utf-8")


def render(name: PromptName, **kwargs: str) -> str:
    template = get_template(name)
    try:
        return template.format(**kwargs)
    except KeyError as e:
        raise ConfigurationError(f"Missing template variable for {name}: {e}") from e
