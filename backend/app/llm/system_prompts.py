"""
Central system prompts for CopilotX.

Kept separate from transport code so prompts can be swapped, A/B tested, or moved to
a config service when the LLM tier becomes its own microservice.
"""

CODE_GENERATION = (
    "You are a senior backend engineer generating production-ready code"
)

CODE_SUMMARIZATION = (
    "You are a senior engineer who explains code clearly and concisely."
)
