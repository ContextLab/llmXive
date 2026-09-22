"""
Project Structure Setup Script

This script creates the foundational directory structure required for the
llmXive automated science pipeline project.
"""
import os
import sys
from pathlib import Path


# Define the directory structure relative to the project root
DIRECTORIES = [
    "src",
    "src/analysis",
    "src/cli",
    "src/lib",
    "src/models",
    "src/services",
    "src/scripts",
    "tests",
    "tests/unit",
    "tests/integration",
    "data",
    "data/raw",
    "data/derived",
    "data/gold_standard",
    "artifacts",
    "specs",
    "specs/001-gene-regulation",
    "specs/001-gene-regulation/contracts",
]

PROJECT_ROOT = Path(__file__).parent.resolve()


def setup_directories():
    """
    Creates all necessary directories for the project structure.
    Ensures idempotency by checking existence before creation.
    """
    created_count = 0
    skipped_count = 0

    for dir_path in DIRECTORIES:
        full_path = PROJECT_ROOT / dir_path
        if full_path.exists():
            skipped_count += 1
            continue
        
        full_path.mkdir(parents=True, exist_ok=True)
        created_count += 1
        # Create __init__.py in Python package directories
        if dir_path.startswith("src") or dir_path.startswith("tests"):
            init_file = full_path / "__init__.py"
            if not init_file.exists():
                init_file.touch()

    return created_count, skipped_count


def main():
    """Entry point for the setup script."""
    print(f"Setting up project structure at: {PROJECT_ROOT}")
    created, skipped = setup_directories()
    print(f"Directories created: {created}")
    print(f"Directories skipped (already exist): {skipped}")
    print("Project structure setup complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
