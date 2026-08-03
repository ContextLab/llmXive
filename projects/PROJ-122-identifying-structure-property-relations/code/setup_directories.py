"""
Setup script to initialize the project directory structure for llmXive.
Creates all required directories for code, data, tests, and state management.
"""
import os
from pathlib import Path


def create_directories():
    """
    Create the standard project directory structure.
    """
    # Define the root directory (assumed to be the project root)
    root = Path.cwd()

    # Define the directory structure to create
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/features",
        "tests",
        "state/projects",
    ]

    created_count = 0
    for dir_path in directories:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")

    print(f"\nSetup complete. {created_count} new directories created.")
    return True


def main():
    """
    Entry point for the script.
    """
    try:
        create_directories()
    except Exception as e:
        print(f"Error during directory creation: {e}")
        raise


if __name__ == "__main__":
    main()