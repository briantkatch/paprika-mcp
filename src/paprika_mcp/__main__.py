"""CLI utilities for paprika-mcp."""

import json
import os
import sys
from getpass import getpass


def setup_credentials():
    """Interactive credential setup."""
    config_dir = os.path.expanduser("~/.paprika-mcp")
    config_file = os.path.join(config_dir, "config.json")

    print("Paprika MCP Server - Credential Setup")
    print("=" * 50)

    # Check if config already exists
    if os.path.exists(config_file):
        print(f"\nConfig file already exists: {config_file}")
        response = input("Overwrite existing credentials? [y/N]: ").strip().lower()
        if response not in ("y", "yes"):
            print("Cancelled.")
            return

    # Get credentials
    print("\nEnter your Paprika account credentials:")
    email = input("Email: ").strip()
    if not email:
        print("Error: Email is required")
        sys.exit(1)

    password = getpass("Password: ")
    if not password:
        print("Error: Password is required")
        sys.exit(1)

    # Create config directory if needed
    os.makedirs(config_dir, exist_ok=True)

    # Write config
    config = {"email": email, "password": password}
    with open(config_file, "w") as f:
        json.dump(config, f, indent=2)

    # Set permissions
    os.chmod(config_file, 0o600)

    print(f"\n✓ Credentials saved to: {config_file}")
    print("  File permissions: 600 (user read/write only)")
    print("\nYou can now start the MCP server with: paprika-mcp")


def main():
    """Main CLI entry point."""
    if len(sys.argv) > 1 and sys.argv[1] == "setup":
        setup_credentials()
    else:
        # Start the server
        from paprika_mcp.server import run

        run()


if __name__ == "__main__":
    main()
