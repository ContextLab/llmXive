"""
Directory Setup Module for llmXive Project PROJ-214.

This module creates the required directory structure for the project.
It ensures that `data/raw`, `data/processed`, `data/models`, and `data/logs`
exist at the repository root relative to the project structure.

This script is idempotent: running it multiple times will not cause errors
if directories already exist.
"""
import os
from pathlib import Path
from config import ensure_directories


def main():
    """
    Main entry point to create project directory structure.

    Creates the following directories under the project root:
    - data/raw
    - data/processed
    - data/models
    - data/logs
    """
    # Define relative paths to create
    # These are relative to the project root.
    # We assume this script is run from the project root or config handles the base.
    paths_to_create = [
        "data/raw",
        "data/processed",
        "data/models",
        "data/logs"
    ]

    print("Initializing project directory structure...")
    created_count = 0
    for rel_path in paths_to_create:
        full_path = Path(rel_path)
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")

    print(f"Directory setup complete. {created_count} new directories created.")
    return 0


if __name__ == "__main__":
    exit(main())