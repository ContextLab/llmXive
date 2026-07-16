"""
Project Structure Setup Module.

This module provides utilities to ensure the required directory structure
for the ambient temperature influence on moral decision speed project.
"""

import os
import sys
from pathlib import Path

# Define the required directory structure relative to the project root
REQUIRED_DIRS = [
    "code",
    "data/raw",
    "data/processed",
    "results/figures",
    "results/logs",
    "results/stats",
    "tests",
]


def ensure_directories(base_path: Path = None) -> bool:
    """
    Ensure all required project directories exist.

    Args:
        base_path: The base path for the project. Defaults to the current
                   working directory.

    Returns:
        True if all directories were successfully created or already exist,
        False otherwise.
    """
    if base_path is None:
        base_path = Path.cwd()

    success = True
    for dir_name in REQUIRED_DIRS:
        dir_path = base_path / dir_name
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            # Verify the directory actually exists and is a directory
            if not dir_path.is_dir():
                print(f"Error: {dir_path} exists but is not a directory.")
                success = False
        except OSError as e:
            print(f"Error creating directory {dir_path}: {e}")
            success = False

    return success


def main():
    """
    Main entry point for the script.
    Creates the project structure from the current working directory.
    """
    print("Setting up project structure...")
    if ensure_directories():
        print("Project structure created successfully.")
        # List created directories for verification
        base_path = Path.cwd()
        for dir_name in REQUIRED_DIRS:
            print(f"  - {base_path / dir_name}")
        sys.exit(0)
    else:
        print("Failed to create project structure.")
        sys.exit(1)


if __name__ == "__main__":
    main()
