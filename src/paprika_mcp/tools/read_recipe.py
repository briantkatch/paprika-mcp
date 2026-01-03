"""Read recipe tool - retrieves full recipe data."""

from typing import Any

from mcp.types import TextContent

from ..utils import get_remote, normalize_string, translate_category_uids


async def read_recipe_tool(args: dict[str, Any]) -> list[TextContent]:
    """Read full recipe data by ID or exact title."""
    recipe_id = args.get("id")
    recipe_title = args.get("title")
    requested_fields = args.get("fields", None)

    if not recipe_id and not recipe_title:
        return [
            TextContent(type="text", text="Error: Must provide either 'id' or 'title'")
        ]

    # Get the remote
    remote = get_remote()

    # If we have an ID, use it directly
    if recipe_id:
        # Need to get all recipes first to find the hash
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

    # Define all available fields and their formatters
    # Translate category UUIDs to names
    category_names = translate_category_uids(
        recipe.categories or [], remote.bearer_token
    )

    all_fields = {
        "name": lambda: [f"# {recipe.name}"],
        "uid": lambda: [f"**UID:** {recipe.uid}"],
        "description": lambda: (
            ["", "## Description", recipe.description] if recipe.description else []
        ),
        "categories": lambda: (
            ["", "## Categories", category_names] if category_names else []
        ),
        "source": lambda: ["", "## Source", recipe.source] if recipe.source else [],
        "source_url": lambda: (
            ["", "## Source URL", recipe.source_url] if recipe.source_url else []
        ),
        "prep_time": lambda: (
            ["", f"**Prep Time:** {recipe.prep_time}"] if recipe.prep_time else []
        ),
        "cook_time": lambda: (
            ["", f"**Cook Time:** {recipe.cook_time}"] if recipe.cook_time else []
        ),
        "total_time": lambda: (
            ["", f"**Total Time:** {recipe.total_time}"] if recipe.total_time else []
        ),
        "servings": lambda: (
            ["", f"**Servings:** {recipe.servings}"] if recipe.servings else []
        ),
        "difficulty": lambda: (
            ["", f"**Difficulty:** {recipe.difficulty}"] if recipe.difficulty else []
        ),
        "rating": lambda: ["", f"**Rating:** {recipe.rating}"] if recipe.rating else [],
        "ingredients": lambda: (
            ["", "## Ingredients", recipe.ingredients] if recipe.ingredients else []
        ),
        "directions": lambda: (
            ["", "## Directions", recipe.directions] if recipe.directions else []
        ),
        "notes": lambda: ["", "## Notes", recipe.notes] if recipe.notes else [],
        "nutritional_info": lambda: (
            ["", "## Nutritional Info", recipe.nutritional_info]
            if recipe.nutritional_info
            else []
        ),
    }

    # Always include name and uid
    output_lines = []
    output_lines.extend(all_fields["name"]())
    output_lines.append("")
    output_lines.extend(all_fields["uid"]())

    # Determine which fields to include
    if requested_fields:
        # Filter to requested fields (excluding name and uid which are always included)
        fields_to_include = [
            f for f in requested_fields if f in all_fields and f not in ["name", "uid"]
        ]
    else:
        # Include all fields
        fields_to_include = [f for f in all_fields.keys() if f not in ["name", "uid"]]

    # Add requested fields in their defined order
    field_order = [
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
        "ingredients",
        "directions",
        "notes",
        "nutritional_info",
    ]

    for field_name in field_order:
        if field_name in fields_to_include:
            output_lines.extend(all_fields[field_name]())

    return [TextContent(type="text", text="\n".join(output_lines))]


# Tool definition
TOOL_DEFINITION = {
    "name": "read_recipe",
    "description": (
        "Read full recipe data by ID or exact title. "
        "Returns recipe fields. Name and UID are always included.\n\n"
        "AVAILABLE FIELDS (all optional except name and uid which are always returned):\n"
        "  - name: Recipe title (always included)\n"
        "  - uid: Recipe unique identifier (always included)\n"
        "  - description: Recipe description/summary\n"
        "  - categories: List of category names\n"
        "  - source: Recipe source (e.g., cookbook name, website)\n"
        "  - source_url: URL where recipe was found\n"
        "  - prep_time: Preparation time\n"
        "  - cook_time: Cooking time\n"
        "  - total_time: Total time (prep + cook)\n"
        "  - servings: Number of servings\n"
        "  - difficulty: Difficulty level\n"
        "  - rating: Recipe rating\n"
        "  - ingredients: List of ingredients with quantities\n"
        "  - directions: Cooking instructions\n"
        "  - notes: Additional notes\n"
        "  - nutritional_info: Nutritional information\n\n"
        "Use the 'fields' parameter to request only specific fields to reduce context size. "
        "For example, fields=['ingredients'] to get only the ingredient list."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "id": {"type": "string", "description": "Recipe UID to read"},
            "title": {
                "type": "string",
                "description": "Exact recipe title to read (alternative to id)",
            },
            "fields": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": [
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
                        "ingredients",
                        "directions",
                        "notes",
                        "nutritional_info",
                    ],
                },
                "description": (
                    "Specific fields to return. Name and UID are always included. "
                    "If not provided, all fields are returned. "
                    "Use this to reduce context size when you only need specific information "
                    "(e.g., just ingredients or just directions)."
                ),
            },
        },
        "required": [],
    },
}
