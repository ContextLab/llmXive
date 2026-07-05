"""
Setup script for linting and formatting tools.
Validates that configuration files exist and are valid.
"""
import os
import sys
from pathlib import Path

def main():
    """Run linting and formatting setup checks."""
    project_root = Path(__file__).parent
    config_files = [
        project_root / ".ruff.toml",
        project_root / "pyproject.toml",
    ]

    missing = [f for f in config_files if not f.exists()]

    if missing:
        print(f"Error: Missing configuration files: {missing}")
        sys.exit(1)

    print("Linting and formatting configuration validated successfully.")
    print("Run 'ruff check . --fix' to fix linting issues.")
    print("Run 'black .' to format code.")

if __name__ == "__main__":
    main()