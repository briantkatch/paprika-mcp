"""Update recipe tool - modifies recipe fields using find/replace."""

import re
from typing import Any

from mcp.types import TextContent

from ..utils import get_remote


async def update_recipe_tool(args: dict[str, Any]) -> list[TextContent]:
    """Update recipe fields using find/replace - DANGEROUS operation."""
    recipe_id = args["id"]
    field = args["field"]
    find = args["find"]
    replace = args["replace"]
    use_regex = args.get("regex", False)

    # Get the remote
    remote = get_remote()

    # Fetch the recipe
    recipe = None
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

    # Get the current field value
    field_value = getattr(recipe, field, None)

    if field_value is None:
        return [
            TextContent(
                type="text",
                text=f"Error: Recipe '{recipe.name}' does not have field '{field}'",
            )
        ]

    # Perform the find/replace
    if use_regex:
        try:
            new_value = re.sub(find, replace, field_value)
        except re.error as e:
            return [
                TextContent(
                    type="text", text=f"Error: Invalid regex pattern '{find}': {str(e)}"
                )
            ]
    else:
        new_value = field_value.replace(find, replace)

    # Check if anything changed
    if new_value == field_value:
        return [
            TextContent(
                type="text",
                text=f"No changes made - pattern '{find}' not found in field '{field}' of recipe '{recipe.name}'",
            )
        ]

    # Update the field
    setattr(recipe, field, new_value)

    # Save the recipe
    try:
        remote.upload_recipe(recipe)
        return [
            TextContent(
                type="text",
                text=f"Successfully updated field '{field}' in recipe '{recipe.name}' (ID: {recipe_id})\n\nOld value:\n{field_value}\n\nNew value:\n{new_value}",
            )
        ]
    except Exception as e:
        return [
            TextContent(
                type="text", text=f"Error updating recipe '{recipe.name}': {str(e)}"
            )
        ]


# Tool definition
TOOL_DEFINITION = {
    "name": "update_recipe",
    "description": (
        "Update recipe fields using find/replace. "
        "This is a DANGEROUS operation that requires user confirmation. "
        "Can update any text field in a recipe."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "id": {"type": "string", "description": "Recipe UID to update"},
            "field": {
                "type": "string",
                "enum": [
                    "name",
                    "ingredients",
                    "directions",
                    "notes",
                    "description",
                    "categories",
                    "source",
                    "source_url",
                    "prep_time",
                    "cook_time",
                    "total_time",
                    "servings",
                    "difficulty",
                    "rating",
                    "nutritional_info",
                ],
                "description": "Field to update",
            },
            "find": {"type": "string", "description": "Text to find in the field"},
            "replace": {"type": "string", "description": "Text to replace it with"},
            "regex": {
                "type": "boolean",
                "description": "Whether to treat 'find' as a regex pattern (default: false)",
                "default": False,
            },
        },
        "required": ["id", "field", "find", "replace"],
    },
}
