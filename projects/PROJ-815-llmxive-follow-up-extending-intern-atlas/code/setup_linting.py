"""
Script to initialize linting and formatting configuration for the project.
This script ensures that ruff and black are properly configured and
provides a helper to run them.
"""
import os
import sys
from pathlib import Path

def main():
    """
    Main entry point to verify configuration files exist.
    In a real CI/CD context, this would be replaced by direct tool invocation.
    """
    project_root = Path(__file__).resolve().parent
    ruff_config = project_root / ".ruff.toml"
    pyproject_config = project_root / "pyproject.toml"

    if not ruff_config.exists():
        print(f"Error: {ruff_config} not found.")
        sys.exit(1)
    
    if not pyproject_config.exists():
        print(f"Error: {pyproject_config} not found.")
        sys.exit(1)

    print("Linting configuration verified:")
    print(f"  - {ruff_config}")
    print(f"  - {pyproject_config}")
    print("\nUsage:")
    print("  To format code:   ruff format .")
    print("  To check code:    ruff check .")
    print("  (Black is handled via ruff format in this setup)")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())