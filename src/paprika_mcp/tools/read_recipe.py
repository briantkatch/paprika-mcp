"""Read recipe tool - retrieves full recipe data."""

from typing import Any

from mcp.types import TextContent

from ..utils import get_remote, normalize_string


async def read_recipe_tool(args: dict[str, Any]) -> list[TextContent]:
    """Read full recipe data by ID or exact title."""
    recipe_id = args.get("id")
    recipe_title = args.get("title")

    if not recipe_id and not recipe_title:
        return [
            TextContent(type="text", text="Error: Must provide either 'id' or 'title'")
        ]

    # Get the remote
    remote = get_remote()

    # If we have an ID, use it directly
    if recipe_id:
        # Need to get all recipes first to find the hash
        for r in remote.recipes:
            if r.uid == recipe_id:
                recipe = r
                break
        if not recipe:
            return [
                TextContent(
                    type="text",
                    text=f"Error: No recipe found with ID '{recipe_id}'",
                )
            ]
    else:
        # Search by title
        # NOTE: This is not optimal - ideally we'd cache the recipe list
        # and search through it, but for now we fetch all recipes
        all_recipes = remote.recipes

        # Normalize the search title
        normalized_search = normalize_string(recipe_title)

        # Find matching recipe
        recipe = None
        for r in all_recipes:
            if normalize_string(r.name) == normalized_search:
                recipe = r
                break

        if not recipe:
            return [
                TextContent(
                    type="text",
                    text=f"Error: No recipe found with title '{recipe_title}'",
                )
            ]

    # Format the recipe data
    output_lines = [
        f"# {recipe.name}",
        "",
        f"**UID:** {recipe.uid}",
    ]

    if recipe.description:
        output_lines.extend(["", "## Description", recipe.description])

    if recipe.categories:
        output_lines.extend(["", "## Categories", ", ".join(recipe.categories)])

    if recipe.source:
        output_lines.extend(["", "## Source", recipe.source])

    if recipe.source_url:
        output_lines.extend(["", "## Source URL", recipe.source_url])

    if recipe.prep_time:
        output_lines.extend(["", f"**Prep Time:** {recipe.prep_time}"])

    if recipe.cook_time:
        output_lines.extend(["", f"**Cook Time:** {recipe.cook_time}"])

    if recipe.total_time:
        output_lines.extend(["", f"**Total Time:** {recipe.total_time}"])

    if recipe.servings:
        output_lines.extend(["", f"**Servings:** {recipe.servings}"])

    if recipe.difficulty:
        output_lines.extend(["", f"**Difficulty:** {recipe.difficulty}"])

    if recipe.rating:
        output_lines.extend(["", f"**Rating:** {recipe.rating}"])

    if recipe.ingredients:
        output_lines.extend(["", "## Ingredients", recipe.ingredients])

    if recipe.directions:
        output_lines.extend(["", "## Directions", recipe.directions])

    if recipe.notes:
        output_lines.extend(["", "## Notes", recipe.notes])

    if recipe.nutritional_info:
        output_lines.extend(["", "## Nutritional Info", recipe.nutritional_info])

    return [TextContent(type="text", text="\n".join(output_lines))]


# Tool definition
TOOL_DEFINITION = {
    "name": "read_recipe",
    "description": (
        "Read full recipe data by ID or exact title. "
        "Returns all recipe fields including categories, times, ingredients, directions, etc."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "id": {"type": "string", "description": "Recipe UID to read"},
            "title": {
                "type": "string",
                "description": "Exact recipe title to read (alternative to id)",
            },
        },
        "required": [],
    },
}
