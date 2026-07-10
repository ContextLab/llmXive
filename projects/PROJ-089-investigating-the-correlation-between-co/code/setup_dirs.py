"""
Module to create the project directory structure.

This script creates the required root directories and subdirectories
for the llmXive research pipeline.
"""
import os
from pathlib import Path


def create_directory_structure(base_path: Path = None) -> None:
    """
    Create the required directory structure for the project.
    
    Args:
        base_path: The root path for the project. Defaults to current working directory.
    """
    if base_path is None:
        base_path = Path.cwd()
    
    # Define the directory structure
    directories = [
        "code",
        "data",
        "tests",
        "contracts",
        "data/raw",
        "data/processed",
        "data/results",
        "data/logs",
    ]
    
    # Create each directory
    created_count = 0
    for dir_path in directories:
        full_path = base_path / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"\nDirectory creation complete. {created_count} new directories created.")
    print(f"Base path: {base_path}")


def main():
    """Entry point for the script."""
    print("Initializing project directory structure...")
    create_directory_structure()


if __name__ == "__main__":
    main()