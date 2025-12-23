#!/bin/bash
# Setup script for paprika-mcp development environment

set -e

echo "Setting up Paprika MCP Server..."

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

echo "Using Python $PYTHON_VERSION"

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
    echo "Error: Python 3.10 or higher is required (Python 3.13 recommended)"
    exit 1
fi

# Set up paprika-recipes first
echo ""
echo "Step 1: Setting up paprika-recipes..."
cd ../paprika-recipes

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment for paprika-recipes..."
    python3 -m venv .venv
fi

source .venv/bin/activate
pip install --upgrade pip
pip install -e .
deactivate

echo "✓ paprika-recipes installed"

# Set up paprika-mcp
echo ""
echo "Step 2: Setting up paprika-mcp..."
cd ../paprika-mcp

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment for paprika-mcp..."
    python3 -m venv .venv
fi

source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev]"

# Install npm dependencies for husky
echo ""
echo "Step 3: Installing pre-commit hooks..."
if command -v npm &> /dev/null; then
    npm install
    echo "✓ Pre-commit hooks installed"
else
    echo "Warning: npm not found. Skipping pre-commit hook installation."
    echo "Install Node.js and run 'npm install' to enable pre-commit hooks."
fi

# Set up credentials
echo ""
echo "Step 4: Configure Paprika credentials..."
CONFIG_DIR="$HOME/.paprika-mcp"
CONFIG_FILE="$CONFIG_DIR/config.json"

mkdir -p "$CONFIG_DIR"

if [ ! -f "$CONFIG_FILE" ]; then
    echo ""
    echo "Enter your Paprika account credentials:"
    read -p "Email: " PAPRIKA_EMAIL
    read -s -p "Password: " PAPRIKA_PASSWORD
    echo ""
    
    cat > "$CONFIG_FILE" << EOF
{
  "email": "$PAPRIKA_EMAIL",
  "password": "$PAPRIKA_PASSWORD"
}
EOF
    chmod 600 "$CONFIG_FILE"
    echo "✓ Credentials saved to $CONFIG_FILE"
else
    echo "✓ Credentials already configured at $CONFIG_FILE"
fi

echo ""
echo "✓ Setup complete!"
echo ""
echo "You can now:"
echo "1. Activate the environment:"
echo "   source .venv/bin/activate"
echo ""
echo "2. Test the server:"
echo "   paprika-mcp"
echo ""
echo "3. Configure your MCP client (e.g., Claude Desktop) with:"
echo "   Command: $PWD/.venv/bin/paprika-mcp"
echo ""
echo "Credentials are stored in: $CONFIG_FILE"
echo "You can also set PAPRIKA_EMAIL and PAPRIKA_PASSWORD environment variables."
