"""
Project structure initialization for Dream-State Learning pipeline.
Creates all required directories for code, tests, data, and logs.
"""
import os
import sys
from pathlib import Path


def create_directories(root_dir: Path = None) -> None:
    """
    Create the complete project directory structure.

    Args:
        root_dir: Base directory for the project. Defaults to current working directory.
    """
    if root_dir is None:
        root_dir = Path.cwd()

    # Define all required directories relative to root
    directories = [
        "code",
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "data",
        "data/raw",
        "data/checkpoints",
        "data/results",
        "data/logs",
    ]

    created_count = 0
    for dir_path in directories:
        full_path = root_dir / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory exists: {full_path}")

    print(f"\nProject structure initialization complete. Created {created_count} new directories.")


if __name__ == "__main__":
    # Execute directory creation when run as a script
    create_directories()
    print("Directory structure verified and ready.")