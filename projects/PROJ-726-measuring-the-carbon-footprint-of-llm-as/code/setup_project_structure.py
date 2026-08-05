"""
Project Structure Initialization Script.

This module creates the necessary directory structure for the llmXive
carbon footprint research project. It ensures that all required folders
exist at the project root level.
"""

import os
import sys
from pathlib import Path


def create_directory_structure(root_path: Path) -> None:
    """
    Create the required directory structure for the project.

    Args:
        root_path: The root directory where the structure should be created.
    """
    required_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "data/outputs",
        "tests",
        "output",
    ]

    created_count = 0
    for dir_name in required_dirs:
        full_path = root_path / dir_name
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")

    if created_count > 0:
        print(f"Successfully created {created_count} new directories.")
    else:
        print("All required directories already exist.")


def main() -> int:
    """
    Main entry point for the project structure setup.

    Returns:
        0 on success, 1 on failure.
    """
    # Determine project root (assumed to be the directory containing this script's parent)
    # Or explicitly use the current working directory if run as a script
    root = Path.cwd()

    print(f"Initializing project structure in: {root}")

    try:
        create_directory_structure(root)
        return 0
    except Exception as e:
        print(f"Error creating directory structure: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())