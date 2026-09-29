"""
Setup script for creating the project directory structure.
Creates all required directories for the llmXive research pipeline.
"""
import os
import sys
from pathlib import Path


def ensure_directory(path: Path) -> None:
    """
    Create a directory if it does not exist.

    Args:
        path: Path object representing the directory to create.
    """
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {path}")
    else:
        print(f"Directory already exists: {path}")


def main() -> int:
    """
    Main entry point for directory setup.

    Creates the following directory structure relative to the project root:
    - code/
    - data/raw/
    - data/derived/
    - tests/
    - specs/
    - results/
    - docs/

    Returns:
        int: Exit code (0 for success, 1 for failure).
    """
    # Determine project root (assume running from project root or script location)
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent

    # Define directories to create
    directories = [
        project_root / "code",
        project_root / "data" / "raw",
        project_root / "data" / "derived",
        project_root / "tests",
        project_root / "specs",
        project_root / "results",
        project_root / "docs",
    ]

    print(f"Setting up directory structure in: {project_root}")

    success = True
    for dir_path in directories:
        try:
            ensure_directory(dir_path)
        except OSError as e:
            print(f"Error creating directory {dir_path}: {e}")
            success = False

    if success:
        print("\nDirectory structure setup complete.")
        return 0
    else:
        print("\nDirectory structure setup completed with errors.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
