"""
Project Setup Script for PROJ-458-quantifying-the-impact-of-dataset-sparsi.

This script creates the required directory structure for the project
as defined in task T001.
"""
import os
import sys
from pathlib import Path


def main():
    """Create the project directory structure."""
    # Define the base directory (project root)
    base_dir = Path(__file__).resolve().parent.parent

    # Define the directories to create relative to the base directory
    directories = [
        "code/utils",
        "data/raw",
        "data/processed",
        "data/results",
        "data/metadata",
        "tests/unit",
        "tests/integration",
        "docs",
    ]

    created_count = 0
    for dir_path_str in directories:
        dir_path = base_dir / dir_path_str
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")

    print(f"\nSetup complete. Created {created_count} new directories.")
    return 0


if __name__ == "__main__":
    sys.exit(main())