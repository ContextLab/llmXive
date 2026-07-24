"""
Setup script for linting and formatting tools (T003).
Ensures configuration files are present and provides instructions for installation.
"""
import os
import sys
from pathlib import Path

def create_config_files():
    """Create or verify ruff and black configuration files."""
    project_root = Path(__file__).parent
    ruff_config = project_root / ".ruff.toml"
    pyproject = project_root / "pyproject.toml"

    # Verify ruff config exists
    if not ruff_config.exists():
        print(f"Error: {ruff_config} not found. Please run this script from the code/ directory.")
        sys.exit(1)

    # Verify pyproject.toml exists with black config
    if not pyproject.exists():
        print(f"Error: {pyproject} not found.")
        sys.exit(1)

    print("Linting configuration files verified:")
    print(f"  - {ruff_config}")
    print(f"  - {pyproject}")

    # Check if tools are installed
    try:
        import ruff
        print("  ✓ ruff is installed")
    except ImportError:
        print("  ✗ ruff is NOT installed. Run: pip install ruff")

    try:
        import black
        print("  ✓ black is installed")
    except ImportError:
        print("  ✗ black is NOT installed. Run: pip install black")

    try:
        import pytest
        print("  ✓ pytest is installed")
    except ImportError:
        print("  ✗ pytest is NOT installed. Run: pip install pytest")

    print("\nTo run linting: ruff check code/")
    print("To format code: black code/")
    print("To run tests: pytest code/tests/")

if __name__ == "__main__":
    create_config_files()
