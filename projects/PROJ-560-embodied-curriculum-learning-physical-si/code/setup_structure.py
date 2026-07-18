"""
Script to set up the project structure.

This script creates the required directories and initializes files.
"""
import os
import sys
from pathlib import Path


def create_directory(path: str) -> None:
    """
    Creates a directory if it doesn't exist.

    Args:
        path (str): Path to the directory.
    """
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    print(f"Created directory: {p.absolute()}")


def main() -> None:
    """Main function to create the project structure."""
    # Create directories
    directories = [
        "code/src",
        "code/tests",
        "data/raw",
        "data/processed",
        "data/synthetic",
        "data/derivation_logs",
        "state/projects/PROJ-560-embodied-curriculum-learning-physical-si"
    ]

    for dir_path in directories:
        create_directory(dir_path)

    # Create __init__.py files
    init_files = [
        "code/src/__init__.py",
        "code/tests/__init__.py"
    ]

    for file_path in init_files:
        p = Path(file_path)
        if not p.exists():
            p.touch()
            print(f"Created empty file: {p.absolute()}")

    print("Project structure setup complete.")


if __name__ == "__main__":
    main()