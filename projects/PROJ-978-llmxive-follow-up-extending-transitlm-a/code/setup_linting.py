"""
Setup script to verify linting and formatting configuration.
This script ensures that ruff and black are properly configured
and can be run on the project.
"""

import os
import sys
from pathlib import Path


def check_file_exists(filepath: str) -> bool:
    """Check if a file exists in the project root."""
    path = Path(filepath)
    if not path.exists():
        print(f"ERROR: Configuration file not found: {filepath}")
        return False
    print(f"OK: Found {filepath}")
    return True


def check_config_content(filepath: str) -> bool:
    """Basic check to ensure config file has content."""
    path = Path(filepath)
    if not path.stat().st_size > 0:
        print(f"ERROR: Configuration file is empty: {filepath}")
        return False
    print(f"OK: {filepath} has content")
    return True


def main():
    """Main entry point for setup verification."""
    project_root = Path(__file__).resolve().parent.parent

    # Check for pyproject.toml
    pyproject_path = project_root / "pyproject.toml"
    if not check_file_exists(str(pyproject_path)):
        return 1

    if not check_config_content(str(pyproject_path)):
        return 1

    # Check for .ruff.toml (optional but recommended)
    ruff_toml_path = project_root / ".ruff.toml"
    # We don't strictly require .ruff.toml if pyproject.toml exists,
    # but we check for it if present.
    if ruff_toml_path.exists():
        if not check_config_content(str(ruff_toml_path)):
            return 1

    # Check for .pre-commit-config.yaml
    pre_commit_path = project_root / ".pre-commit-config.yaml"
    if not check_file_exists(str(pre_commit_path)):
        print("WARNING: .pre-commit-config.yaml not found. Pre-commit hooks not configured.")
    else:
        if not check_config_content(str(pre_commit_path)):
            return 1

    print("\nLinting and formatting configuration verified successfully.")
    print("To run linter: ruff check .")
    print("To run formatter: black .")
    print("To install pre-commit hooks: pre-commit install")
    return 0


if __name__ == "__main__":
    sys.exit(main())