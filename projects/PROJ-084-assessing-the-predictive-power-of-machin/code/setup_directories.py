"""
Script to create the required project directory structure for llmXive.

This script ensures the existence of:
- code/
- data/raw/
- data/processed/
- data/results/
- tests/

It is idempotent and safe to run multiple times.
"""
import os
from pathlib import Path

def main():
    """Create the standard project directory structure."""
    # Define the project root (assumed to be the directory containing this script's parent,
    # or we can assume the script is run from the project root).
    # Based on the API surface, this script is at code/setup_directories.py.
    # We need to create directories relative to the project root.
    # If this script is run via `python code/setup_directories.py`, the cwd is usually the project root.
    # To be safe, we resolve the project root as the parent of the 'code' directory.
    
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    project_root = code_dir.parent

    # Define the directories to create
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/results",
        "tests"
    ]

    created_count = 0
    for dir_name in directories:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")

    if created_count == 0:
        print("All required directories already exist.")
    else:
        print(f"Successfully created {created_count} new directories.")

    # Verify structure
    print("\nProject Directory Structure:")
    print(project_root)
    for d in directories:
        p = project_root / d
        print(f"  {p}/ (exists: {p.exists()})")

if __name__ == "__main__":
    main()
