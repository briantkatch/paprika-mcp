"""Utility functions for paprika-mcp server."""

import json
import logging
import os
import unicodedata
from typing import Any

from paprika_recipes.cache import DirectoryCache
from paprika_recipes.remote import Remote

logger = logging.getLogger(__name__)


def get_credentials() -> tuple[str, str]:
    """Get Paprika credentials from environment variables or config file.

    Priority:
    1. PAPRIKA_EMAIL and PAPRIKA_PASSWORD environment variables
    2. ~/.paprika-mcp/config.json file

    Raises:
        ValueError: If credentials are not configured
    """
    # Check environment variables first
    email = os.environ.get("PAPRIKA_EMAIL")
    password = os.environ.get("PAPRIKA_PASSWORD")

    if email and password:
        return email, password

    # Check config file
    config_path = os.path.expanduser("~/.paprika-mcp/config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path) as f:
                config = json.load(f)
                email = config.get("email")
                password = config.get("password")
                if email and password:
                    return email, password
        except (OSError, json.JSONDecodeError) as e:
            logger.warning(f"Failed to read config file: {e}")

    raise ValueError(
        "Paprika credentials not found. Set PAPRIKA_EMAIL and PAPRIKA_PASSWORD "
        "environment variables, or create ~/.paprika-mcp/config.json with "
        '{"email": "your@email.com", "password": "yourpassword"}'
    )


def get_user_agent() -> str | None:
    """Get User-Agent string from environment or config file.

    Priority:
    1. PAPRIKA_USER_AGENT environment variable
    2. user_agent field in ~/.paprika-mcp/config.json

    Note: If not configured here, the Remote class will auto-detect from
    the installed Paprika app.

    Returns:
        User-Agent string or None (which triggers auto-detection in Remote)
    """
    # Check environment variable first
    user_agent = os.environ.get("PAPRIKA_USER_AGENT")
    if user_agent:
        return user_agent

    # Check config file
    config_path = os.path.expanduser("~/.paprika-mcp/config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path) as f:
                config = json.load(f)
                user_agent = config.get("user_agent")
                if user_agent:
                    return user_agent
        except (OSError, json.JSONDecodeError) as e:
            logger.warning(f"Failed to read user_agent from config file: {e}")

    return None


def get_remote() -> Remote:
    """Get authenticated Remote instance using stored credentials.

    The Remote class uses a DirectoryCache to store recipe data locally:
    - Recipe metadata (list of UIDs/hashes) is always fetched fresh from the API
    - Individual recipe details are cached in ~/.paprika-mcp/cache/
    - Cached recipes are keyed by UID and validated by hash
    - If a recipe's hash matches the cache, the cached version is used
    - If hash differs or not cached, recipe is fetched from API and cached

    Note: Remote.recipes is a generator that makes API calls. If you need to
    iterate multiple times or access by index, convert to list first.

    Raises:
        ValueError: If credentials are not configured
        PaprikaError: If authentication fails (check credentials)
        RequestError: If API request fails (network/server issue)
    """
    email, password = get_credentials()
    user_agent = get_user_agent()

    # Use cache to avoid re-downloading recipes
    cache_dir = os.path.expanduser("~/.paprika-mcp/cache")
    os.makedirs(cache_dir, exist_ok=True)
    cache = DirectoryCache(cache_dir)

    try:
        # Use 30 second timeout to prevent hanging on network issues
        remote = Remote(email, password, cache=cache, user_agent=user_agent, timeout=30)
        # Test authentication by accessing bearer_token
        _ = remote.bearer_token
        return remote
    except Exception as e:
        logger.error(f"Failed to authenticate with Paprika API: {e}")
        logger.error(
            "Please verify your credentials in ~/.paprika-mcp/config.json "
            "or PAPRIKA_EMAIL/PAPRIKA_PASSWORD environment variables. "
            "You may also need to set a user_agent to mimic the official Paprika app."
        )
        raise


def normalize_string(text: str) -> str:
    """Normalize unicode string for comparison.

    Uses NFD normalization to decompose accented characters,
    making comparisons work across different unicode representations.
    """
    return unicodedata.normalize("NFD", text).lower()


def search_in_text(
    text: str, query: str, context_lines: int = 2
) -> list[dict[str, Any]]:
    """Search for query in text and return matches with context.

    Returns list of dicts with 'line', 'match', and 'context' keys.
    """
    if not text:
        return []

    matches = []
    lines = text.split("\n")
    query_lower = query.lower()

    for i, line in enumerate(lines):
        if query_lower in line.lower():
            # Get context lines before and after
            start = max(0, i - context_lines)
            end = min(len(lines), i + context_lines + 1)
            context = "\n".join(lines[start:end])

            matches.append({"line": i + 1, "match": line.strip(), "context": context})

    return matches
