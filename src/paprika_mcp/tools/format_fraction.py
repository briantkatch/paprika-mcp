"""Format fraction tool - converts fractions to Unicode characters."""

import unicodedata
from typing import Any

from mcp.types import TextContent


def format_fraction(fraction_str: str) -> str:
    """Format a fraction string to unicode fraction characters.

    Args:
        fraction_str: Fraction in the form "1/4", "31/200", or already formatted like "¼"

    Returns:
        Unicode formatted fraction (e.g., "¼" or "³¹⁄₂₀₀")
    """
    # Strip whitespace
    fraction_str = fraction_str.strip()

    # Check if it's already a unicode fraction - if so, return as-is
    # Unicode fractions are in these ranges:
    # U+00BC-00BE (¼ ½ ¾)
    # U+2150-215E (various fractions)
    # Also check for composed fractions (superscript + U+2044 + subscript)
    if any(unicodedata.category(c) in ("No",) or c == "\u2044" for c in fraction_str):
        return fraction_str

    # Map of common fractions to their unicode characters
    common_fractions = {
        "1/4": "¼",
        "1/2": "½",
        "3/4": "¾",
        "1/7": "⅐",
        "1/9": "⅑",
        "1/10": "⅒",
        "1/3": "⅓",
        "2/3": "⅔",
        "1/5": "⅕",
        "2/5": "⅖",
        "3/5": "⅗",
        "4/5": "⅘",
        "1/6": "⅙",
        "5/6": "⅚",
        "1/8": "⅛",
        "3/8": "⅜",
        "5/8": "⅝",
        "7/8": "⅞",
    }

    # Check if it's a common fraction
    if fraction_str in common_fractions:
        return common_fractions[fraction_str]

    # Parse the fraction
    if "/" not in fraction_str:
        raise ValueError("Fraction must contain a '/' character")

    parts = fraction_str.split("/")
    if len(parts) != 2:
        raise ValueError("Fraction must be in the form 'numerator/denominator'")

    numerator, denominator = parts

    # Validate that both parts are numbers
    try:
        int(numerator)
        int(denominator)
    except ValueError as e:
        raise ValueError("Numerator and denominator must be integers") from e

    # Build using superscript + fraction slash + subscript
    superscript_digits = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")
    subscript_digits = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")

    superscript_num = numerator.translate(superscript_digits)
    subscript_den = denominator.translate(subscript_digits)
    fraction_slash = "\u2044"  # U+2044 FRACTION SLASH

    return f"{superscript_num}{fraction_slash}{subscript_den}"


async def format_fraction_tool(args: dict[str, Any]) -> list[TextContent]:
    """Format a fraction to unicode."""
    fraction_str = args["fraction"]

    try:
        formatted = format_fraction(fraction_str)
        return [
            TextContent(
                type="text",
                text=f"Formatted fraction: {formatted}\n\nOriginal: {fraction_str}\nFormatted: {formatted}",
            )
        ]
    except ValueError as e:
        return [
            TextContent(
                type="text",
                text=f"Error formatting fraction '{fraction_str}': {str(e)}",
            )
        ]


# Tool definition
TOOL_DEFINITION = {
    "name": "format_fraction",
    "description": (
        "Format a fraction string to unicode fraction characters. "
        "Converts simple fractions like '1/4' to '¼' or complex ones like '31/200' to '³¹⁄₂₀₀'. "
        "Handles already-formatted unicode fractions and strips whitespace. "
        "This tool does not require server connectivity and can be used for testing."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "fraction": {
                "type": "string",
                "description": "Fraction in the form 'numerator/denominator' (e.g., '1/4', ' 31 / 200 '), or already formatted unicode",
            }
        },
        "required": ["fraction"],
    },
}
