"""Search recipes tool - searches recipe text by keyword."""

from typing import Any

from mcp.types import TextContent

from ..utils import get_remote, search_in_text


async def search_recipes_tool(args: dict[str, Any]) -> list[TextContent]:
    """Search recipes by text across multiple fields."""
    query = args["query"]
    fields = args.get("fields", None)
    context_lines = args.get("context_lines", 2)

    # Get the remote
    remote = get_remote()

    # Fetch all recipes
    recipes = remote.recipes

    results = []

    for recipe in recipes:
        # Determine which fields to search
        searchable_fields = {
            "name": recipe.name,
            "ingredients": recipe.ingredients,
            "categories": ", ".join(recipe.categories) if recipe.categories else "",
            "directions": recipe.directions,
            "notes": recipe.notes or "",
        }

        # Filter to requested fields if specified
        if fields:
            searchable_fields = {
                k: v for k, v in searchable_fields.items() if k in fields
            }

        # Search each field
        for field_name, field_text in searchable_fields.items():
            if not field_text:
                continue

            matches = search_in_text(field_text, query, context_lines)
            if matches:
                results.append(
                    {
                        "recipe_id": recipe.uid,
                        "recipe_title": recipe.name,
                        "field": field_name,
                        "matches": matches,
                    }
                )

    if not results:
        return [TextContent(type="text", text=f"No recipes found matching '{query}'")]

    # Format results
    output_lines = [f"Found {len(results)} matches for '{query}':\n"]

    for result in results:
        output_lines.append(
            f"\n## {result['recipe_title']} (ID: {result['recipe_id']})"
        )
        output_lines.append(f"Field: {result['field']}")
        output_lines.append("Matches:")
        for match in result["matches"]:
            output_lines.append(f"  Line {match['line']}: {match['context']}")

    return [TextContent(type="text", text="\n".join(output_lines))]


# Tool definition
TOOL_DEFINITION = {
    "name": "search_recipes",
    "description": (
        "Search recipes by text across title, ingredients, categories, directions, or notes. "
        "Returns recipe IDs, titles, and context for each match."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Text to search for in recipes"},
            "fields": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": [
                        "name",
                        "ingredients",
                        "categories",
                        "directions",
                        "notes",
                    ],
                },
                "description": "Specific fields to search in. If not provided, searches all fields (name, ingredients, categories, directions, notes)",
            },
            "context_lines": {
                "type": "integer",
                "description": "Number of lines of context to show around matches (default: 2)",
                "default": 2,
            },
        },
        "required": ["query"],
    },
}
