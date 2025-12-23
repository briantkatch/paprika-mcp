"""User preferences prompt - loads user context from ~/.paprika-mcp/prompt.md."""

from pathlib import Path
from typing import Any

from mcp.types import GetPromptResult, PromptMessage, TextContent


async def user_preferences_prompt(args: dict[str, Any]) -> GetPromptResult:
    """Load user preferences from ~/.paprika-mcp/prompt.md."""
    prompt_path = Path.home() / ".paprika-mcp" / "prompt.md"

    if not prompt_path.exists():
        return GetPromptResult(
            description="User preferences not configured",
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text="No user preferences file found at ~/.paprika-mcp/prompt.md",
                    ),
                )
            ],
        )

    try:
        content = prompt_path.read_text()
        return GetPromptResult(
            description="User preferences and context",
            messages=[
                PromptMessage(
                    role="user", content=TextContent(type="text", text=content)
                )
            ],
        )
    except Exception as e:
        return GetPromptResult(
            description="Error loading user preferences",
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=f"Error reading ~/.paprika-mcp/prompt.md: {str(e)}",
                    ),
                )
            ],
        )


# Prompt definition
PROMPT_DEFINITION = {
    "name": "user_preferences",
    "description": (
        "Load user preferences and high-level context from ~/.paprika-mcp/prompt.md. "
        "This can include dietary restrictions, favorite ingredients, or other helpful context."
    ),
}
