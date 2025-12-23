"""Prompts module - exports all MCP prompt implementations."""

from .user_preferences import PROMPT_DEFINITION as USER_PREFS_DEF
from .user_preferences import user_preferences_prompt

# Export all prompts and their definitions
PROMPTS = {
    "user_preferences": {
        "definition": USER_PREFS_DEF,
        "handler": user_preferences_prompt,
    },
}

__all__ = [
    "PROMPTS",
    "user_preferences_prompt",
]
