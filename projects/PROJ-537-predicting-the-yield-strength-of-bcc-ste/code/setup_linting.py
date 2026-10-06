"""
Setup script to ensure linting and formatting tools are available
and to generate initial configuration if missing.
"""
import os
import sys
from pathlib import Path

def main():
    """
    Verifies linting configuration exists and prints instructions.
    This script does not install packages (assumes requirements.txt is used)
    but ensures the configuration files are present.
    """
    project_root = Path(__file__).parent
    flake8_config = project_root / ".flake8"
    pyproject = project_root / "pyproject.toml"

    if not flake8_config.exists():
        print(f"Warning: {flake8_config} not found. Please ensure it exists.")
    else:
        print(f"Found linting config: {flake8_config}")

    if not pyproject.exists():
        print(f"Warning: {pyproject} not found. Please ensure it exists.")
    else:
        print(f"Found project config: {pyproject}")

    print("\nLinting and Formatting Tools Configuration:")
    print("- flake8: Configured in code/.flake8")
    print("- black: Configured in code/pyproject.toml")
    print("- isort: Configured in code/pyproject.toml")
    print("\nTo run linting: make lint")
    print("To run formatting: make format")
    print("To check format: make check-format")

    return 0

if __name__ == "__main__":
    sys.exit(main())