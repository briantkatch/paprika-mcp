# Paprika MCP Server

A Model Context Protocol (MCP) server for the Paprika Recipe Manager, allowing AI assistants to search, read, and update recipes.

## Features

- **Search Recipes**: Search across recipe titles, ingredients, categories, directions, and notes with context
- **Read Recipes**: Get full recipe data including all metadata, ingredients, and directions
- **Update Recipes**: Safely update recipe fields using find/replace (requires user confirmation)

## Prerequisites

1. Python 3.10 or higher (Python 3.13 recommended)
2. A Paprika account with recipes
3. Node.js (for pre-commit hooks, optional)

## Quick Start

Run the setup script to install everything and configure credentials:

```bash
cd paprika-mcp
./setup.sh
```

This will:
1. Install paprika-mcp with dependencies
2. Set up pre-commit hooks (if npm available)

## Manual Installation

If you prefer manual setup:

### 1. Install paprika-recipes

```bash
cd ../paprika-recipes
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
deactivate
```

### 2. Install paprika-mcp

```bash
cd ../paprika-mcp
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 3. Configure credentials

**Option 1: Interactive setup**

```bash
source .venv/bin/activate
paprika-mcp setup
```

**Option 2: Manual config file**

Create `~/.paprika-mcp/config.json`:

```json
{
  "email": "your@email.com",
  "password": "yourpassword"
}
```

Set permissions:
```bash
chmod 600 ~/.paprika-mcp/config.json
```

**Option 3: Environment variables**

```bash
export PAPRIKA_EMAIL="your@email.com"
export PAPRIKA_PASSWORD="yourpassword"
```

## Credential Management

The server uses a credential flow designed for MCP stdio transport:

**Priority order:**
1. `PAPRIKA_EMAIL` and `PAPRIKA_PASSWORD` environment variables
2. `~/.paprika-mcp/config.json` file

**Note**: This server manages credentials independently from the paprika-recipes CLI tool's keyring storage. This simplifies the credential flow for MCP stdio transport where the process is spawned by the AI app.

## User-Agent

If you have Paprika for Mac installed, the fork of the `paprika-recipes` Python package should automatically create a suitable User-Agent string. Otherwise, you might have to set the `PAPRIKA_USER_AGENT` environment variable or the "user_agent" property in `config.json`.

## Usage

### As an MCP Server

Add to your MCP client configuration (e.g., Claude Desktop's `~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "paprika": {
      "command": "/Users/yourusername/Developer/paprika-mcp/.venv/bin/paprika-mcp"
    }
  }
}
```

Or use environment variables:

```json
{
  "mcpServers": {
    "paprika": {
      "command": "/Users/yourusername/Developer/paprika-mcp/.venv/bin/paprika-mcp",
      "env": {
        "PAPRIKA_EMAIL": "your@email.com",
        "PAPRIKA_PASSWORD": "yourpassword"
      }
    }
  }
}
```

### Available Tools

#### format_fraction

Format a fraction string to unicode fraction characters. **This tool is local-only** and doesn't require Paprika server connectivity - useful for testing.

**Parameters:**
- `fraction` (required): Fraction in the form "numerator/denominator" (e.g., "1/4", " 31 / 200 "), or already formatted unicode

**Features:**
- Handles already-formatted unicode fractions (returns them as-is)
- Strips whitespace from input
- Converts common fractions to dedicated unicode characters
- Composes complex fractions using superscript/subscript digits

**Examples:**
```json
{
  "fraction": "1/4"
}
```
Returns: `¼`

```json
{
  "fraction": " 31 / 200 "
}
```
Returns: `³¹⁄₂₀₀` (whitespace stripped)

```json
{
  "fraction": "¼"
}
```
Returns: `¼` (already formatted, returned as-is)

Common fractions (1/4, 1/2, 3/4, 1/3, 2/3, etc.) use dedicated Unicode characters. Complex fractions are composed using superscript numerator + fraction slash (⁄) + subscript denominator.

#### search_recipes

Search for recipes by text across multiple fields.

**Parameters:**
- `query` (required): Text to search for
- `fields` (optional): Array of fields to search in: `["name", "ingredients", "categories", "directions", "notes"]`
- `context_lines` (optional): Number of context lines around matches (default: 2)

**Example:**
```json
{
  "query": "chicken",
  "fields": ["name", "ingredients"],
  "context_lines": 2
}
```

#### read_recipe

Read full recipe data by ID or title.

**Parameters:**
- `id` or `title` (one required): Recipe UUID or exact recipe name

**Note:** Title matching uses Unicode normalization (NFD), so it works correctly with accented characters regardless of their unicode representation (e.g., "café" will match "café").

**Example:**
```json
{
  "id": "RECIPE-UUID-HERE"
}
```

or

```json
{
  "title": "Chocolate Chip Cookies"
}
```

### User Preferences (Prompts)

You can provide context to the AI about how you want it to work with your recipes by creating a `~/.paprika-mcp/prompt.md` file. This will be automatically loaded as a prompt when the MCP server starts.

**Example prompt file:**
```markdown
# Recipe Management Preferences

- Always preserve source URLs and attribution
- Prefer metric measurements
- I'm cooking for 2 people typically
- I avoid peanuts (allergy)
- Categorize using: Breakfast, Lunch, Dinner, Desserts, Snacks
```

See [`prompt.example.md`](prompt.example.md) for a complete template.

#### update_recipe

Update a recipe field using find/replace.

**⚠️ DANGEROUS**: This tool modifies recipe data. User confirmation is recommended before execution.

**Parameters:**
- `id` (required): Recipe UUID
- `field` (required): Field to update (name, ingredients, directions, notes, etc.)
- `find` (required): Text to find
- `replace` (required): Text to replace with
- `regex` (optional): Treat find pattern as regex (default: false)

**Example:**
```json
{
  "id": "RECIPE-UUID-HERE",
  "field": "ingredients",
  "find": "1 cup sugar",
  "replace": "3/4 cup sugar"
}
```

### Code Changes and Rebuilding

The package is installed in **editable mode** (`pip install -e .`), so:

- **✓ No rebuild needed**: Changes to `.py` files are immediately available
- **⚠️ Restart required**: MCP clients cache the stdio process - restart VS Code or your MCP client to pick up changes
- **↻ Reinstall needed**: Only for `pyproject.toml` or entry point changes

Force reinstall if needed:
```bash
.venv/bin/pip install -e . --force-reinstall --no-deps
```

### Pre-commit Hooks

Pre-commit hooks run automatically via Husky when you commit. They:
1. Only run on staged Python files
2. Run isort, black, and ruff
3. Auto-fix issues and re-stage files

To install hooks manually:
```bash
npm install
```

## Security Notes

- Credentials are stored in plain text in `~/.paprika-mcp/config.json`
- Environment variables (`PAPRIKA_EMAIL`, `PAPRIKA_PASSWORD`) are also supported

## License

MIT

## Credits

Built on top of [paprika-recipes](https://github.com/briantkatch/paprika-recipes) originally by Adam Coddington.
