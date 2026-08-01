"""
Project Structure Initialization Script for llmXive Pipeline.

This script creates the required directory structure for the statistical
analysis of publicly available textual data for detecting cognitive decline.

It ensures all necessary directories for code, data (raw, processed, interim, results),
tests (unit, contract, integration), and specifications exist.
"""
import os
import sys
from pathlib import Path

# Define the required directory structure relative to the project root
REQUIRED_DIRS = [
    "code",
    "data/raw",
    "data/processed",
    "data/interim",
    "data/results",
    "tests/unit",
    "tests/contract",
    "tests/integration",
    "specs/001-statistical-cognitive-decline/contracts",
]

def create_directory(dir_path: str) -> bool:
    """
    Create a directory if it does not exist.
    
    Args:
        dir_path: Relative path to the directory from the project root.
        
    Returns:
        True if the directory was created or already exists, False on failure.
    """
    full_path = Path(dir_path)
    try:
        full_path.mkdir(parents=True, exist_ok=True)
        return True
    except OSError as e:
        print(f"Error creating directory {dir_path}: {e}", file=sys.stderr)
        return False

def main():
    """
    Main entry point to initialize the project structure.
    
    Creates all directories defined in REQUIRED_DIRS.
    Prints a summary of created/existing directories.
    """
    project_root = Path.cwd()
    created_count = 0
    existing_count = 0
    failed_count = 0

    print(f"Initializing project structure in: {project_root}")
    print("-" * 50)

    for dir_name in REQUIRED_DIRS:
        full_path = project_root / dir_name
        
        if full_path.exists():
            print(f"[EXIST] {dir_name}")
            existing_count += 1
        else:
            if create_directory(dir_name):
                print(f"[CREATED] {dir_name}")
                created_count += 1
            else:
                print(f"[FAILED] {dir_name}")
                failed_count += 1

    print("-" * 50)
    print(f"Summary: {created_count} created, {existing_count} existing, {failed_count} failed")
    
    if failed_count > 0:
        sys.exit(1)
    else:
        print("Project structure initialization complete.")
        sys.exit(0)

if __name__ == "__main__":
    main()