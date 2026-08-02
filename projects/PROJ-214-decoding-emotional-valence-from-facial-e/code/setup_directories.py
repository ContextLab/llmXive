"""
setup_directories.py

Creates the required directory structure for the project.
This script ensures that data/raw, data/processed, data/models, and data/logs
exist at the repository root. It is idempotent (safe to run multiple times).
"""

import os
from pathlib import Path


def main():
    """Create the standard project directory structure."""
    # Determine the project root (parent of the 'code' directory)
    # Assuming this script is located in code/, we go up one level.
    project_root = Path(__file__).resolve().parent.parent

    # Define the directories to create
    directories = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "models",
        project_root / "data" / "logs",
    ]

    for dir_path in directories:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
        else:
            print(f"Directory already exists: {dir_path}")

    print("Directory structure setup complete.")


if __name__ == "__main__":
    main()
