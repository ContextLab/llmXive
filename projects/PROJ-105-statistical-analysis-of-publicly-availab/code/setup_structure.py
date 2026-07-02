"""
Project Structure Setup Script

This script creates the required directory tree and placeholder files
for the Flight Delay Analysis project as specified in the implementation plan.
"""
import os
import sys
from pathlib import Path


def main():
    """Create the project directory structure and placeholder files."""
    project_root = Path(__file__).parent.parent
    print(f"Setting up project structure at: {project_root}")

    # Define directories to create
    directories = [
        "code/tests",
        "data/raw",
        "data/processed",
        "data/results",
        "docs",
        "code/contracts",
        "tests/unit",
        "tests/integration",
        "tests/contract",
    ]

    # Define files to create
    files = [
        "code/__init__.py",
        "tests/__init__.py",
        "data/.gitkeep",
        "docs/.gitkeep",
    ]

    created_count = 0
    skipped_count = 0

    # Create directories
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            skipped_count += 1

    # Create files
    for file_path in files:
        full_path = project_root / file_path
        if not full_path.exists():
            full_path.touch()
            print(f"Created file: {full_path}")
            created_count += 1
        else:
            skipped_count += 1

    print(f"\nSetup complete. Created {created_count} items, skipped {skipped_count} existing items.")
    return 0


if __name__ == "__main__":
    sys.exit(main())