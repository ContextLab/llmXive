"""
Linting setup utilities for the project.
Validates configuration files for ruff and black.
"""
import os
import sys
from pathlib import Path

def check_config_files() -> bool:
    """
    Verify that linting configuration files exist in the project root.

    Returns:
        bool: True if all required config files are present, False otherwise.
    """
    project_root = Path(__file__).resolve().parent.parent
    required_files = [
        "pyproject.toml",
        ".pre-commit-config.yaml",
    ]

    missing = []
    for filename in required_files:
        if not (project_root / filename).exists():
            missing.append(filename)

    if missing:
        print(f"ERROR: Missing linting configuration files: {', '.join(missing)}")
        print("Please run the setup task to generate these files.")
        return False

    print("Linting configuration files found.")
    return True

if __name__ == "__main__":
    success = check_config_files()
    sys.exit(0 if success else 1)