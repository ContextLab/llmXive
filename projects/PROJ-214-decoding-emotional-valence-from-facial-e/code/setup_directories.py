"""
Directory Setup Module for PROJ-214-decoding-emotional-valence-from-facial-e.

This script creates the required project directory structure:
- code/
- tests/
- data/raw
- data/processed
- data/models
- data/logs

It ensures that the project adheres to the path conventions defined in the
research plan and tasks.md.
"""

import os
from pathlib import Path


def main() -> None:
    """Create all required project directories."""
    # Define the project root (assumed to be the directory containing this script's parent)
    # However, per instructions, paths are relative to the project root.
    # We assume this script is run from the project root or we resolve relative to __file__.
    project_root = Path(__file__).resolve().parent.parent

    # Define required directories relative to project root
    required_dirs = [
        "code",
        "tests",
        "data/raw",
        "data/processed",
        "data/models",
        "data/logs",
        # Ensure subdirectories for tests exist if not already created by other tasks
        "tests/unit",
        "tests/integration",
    ]

    created_count = 0
    skipped_count = 0

    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            # Only log if it's not just a parent directory check (i.e., if it's a leaf we care about)
            # For this task, we just ensure they exist.
            skipped_count += 1

    print(f"Directory setup complete. Created: {created_count}, Already exists: {skipped_count}")


if __name__ == "__main__":
    main()