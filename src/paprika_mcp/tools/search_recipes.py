"""Search recipes tool - searches recipe text by keyword."""

from typing import Any

from mcp.types import TextContent

from ..utils import get_categories, get_remote, search_in_text, translate_category_uids


async def search_recipes_tool(args: dict[str, Any]) -> list[TextContent]:
    """Search recipes by text across multiple fields."""
    query = args["query"]
    fields = args.get("fields", None)
    context_lines = args.get("context_lines", 2)
    page = args.get("page", 1)
    page_size = args.get("page_size", 20)
    regex = args.get("regex", False)
    category_filter = args.get("category", None)

    # Get the remote
    remote = get_remote()

    # Fetch all recipes (excluding trashed) and sort alphabetically
    all_recipes = [r for r in remote.recipes if not r.in_trash]
    all_recipes.sort(key=lambda r: r.name.lower())

    # Get category mappings for translating UUIDs to names
    categories_data = get_categories(remote.bearer_token)
    category_name_to_uid = categories_data["name_to_uid"]

    results = []

    for recipe in all_recipes:
        # Filter by category if specified
        if category_filter:
            # Try to match by category name (case-insensitive)
            category_uid = category_name_to_uid.get(category_filter.lower())
            if category_uid:
                # Match by resolved UID
                if category_uid not in (recipe.categories or []):
                    continue
            else:
                # No matching category name found, skip this recipe
                continue

        # Translate category UUIDs to names for searching
        category_names = translate_category_uids(
            recipe.categories or [], remote.bearer_token
        )

        # Determine which fields to search
        searchable_fields = {
            "name": recipe.name,
            "ingredients": recipe.ingredients,
            "categories": category_names,  # Now using translated names
            "directions": recipe.directions,
            "notes": recipe.notes or "",
        }

        # Filter to requested fields if specified
        if fields:
            searchable_fields = {
                k: v for k, v in searchable_fields.items() if k in fields
            }

        # For empty query, match all recipes
        if not query:
            results.append(
                {
                    "recipe_id": recipe.uid,
                    "recipe_title": recipe.name,
                    "field": "all",
                    "matches": [],
                }
            )
            continue

        # Search each field
        for field_name, field_text in searchable_fields.items():
            if not field_text:
                continue

            matches = search_in_text(field_text, query, context_lines, regex=regex)
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
        query_text = query if query else "(empty query)"
        category_text = f" in category '{category_filter}'" if category_filter else ""
        return [
            TextContent(
                type="text",
                text=f"No recipes found matching '{query_text}'{category_text}",
            )
        ]

    # Count unique recipes
    unique_recipes = len({r["recipe_id"] for r in results})

    # Apply pagination
    total_pages = (len(results) + page_size - 1) // page_size
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_results = results[start_idx:end_idx]

    # Format results
    query_text = f"'{query}'" if query else "all recipes"
    category_text = f" in category '{category_filter}'" if category_filter else ""
    regex_text = " (regex)" if regex else ""
    output_lines = [
        f"Found {unique_recipes} recipes with {len(results)} total matches for {query_text}{regex_text}{category_text}",
        f"Page {page} of {total_pages} (showing {len(paginated_results)} results)\n",
    ]

    for result in paginated_results:
        output_lines.append(
            f"\n## {result['recipe_title']} (ID: {result['recipe_id']})"
        )
        if result["field"] != "all":
            output_lines.append(f"Field: {result['field']}")
            output_lines.append("Matches:")
            for match in result["matches"]:
                output_lines.append(f"  Line {match['line']}: {match['context']}")

    if page < total_pages:
        output_lines.append(
            f"\n... Use page={page + 1} to see more results (up to page {total_pages})"
        )

    return [TextContent(type="text", text="\n".join(output_lines))]


# Tool definition
TOOL_DEFINITION = {
    "name": "search_recipes",
    "description": (
        "Search recipes by text across title, ingredients, categories, directions, or notes. "
        "Returns recipe IDs, titles, and context for each match. "
        "Use an empty query ('') to get all recipes. "
        "Results are paginated and sorted alphabetically. "
        "Only non-trashed recipes are included.\n\n"
        "REGEX SEARCH: Set regex=true to use regular expressions. "
        "This is especially useful for matching singular/plural forms of ingredients:\n"
        "  - 'cherr(y|ies)' matches both 'cherry' and 'cherries'\n"
        "  - 'bananas?' matches 'banana' or 'bananas'\n"
        "  - 'tomat(o|oes)' matches 'tomato' or 'tomatoes'\n"
        "  - '(beef|chicken|pork)' matches any of these meats\n\n"
        "CATEGORY SEARCH: Use the 'category' parameter to filter by category name (not UUID). "
        "Use list_categories tool first to see available categories."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Text to search for in recipes. Use empty string '' to get all recipes.",
            },
            "regex": {
                "type": "boolean",
                "description": (
                    "If true, treat query as a regex pattern. "
                    "Useful for matching singular/plural: 'cherr(y|ies)', 'bananas?', 'tomat(o|oes)'. "
                    "Default: false"
                ),
                "default": False,
            },
            "category": {
                "type": "string",
                "description": (
                    "Filter results to only recipes in this category. "
                    "Use the category NAME (not UUID). "
                    "Use list_categories tool to see available categories."
                ),
            },
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
            "page": {
                "type": "integer",
                "description": "Page number for pagination (default: 1)",
                "default": 1,
            },
            "page_size": {
                "type": "integer",
                "description": "Number of results per page (default: 20)",
                "default": 20,
            },
        },
        "required": ["query"],
    },
}
