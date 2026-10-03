"""
Script to initialize the project directory structure for the network synchronization study.
Executes the required mkdir -p commands to create src, tests, data, results, and subdirectories.
"""
import os
import sys
from pathlib import Path

def main():
    """Create the standard project directory structure."""
    # Define the relative paths to create based on tasks.md T001
    # Note: The task specifies paths relative to the project root.
    # We assume this script runs from the project root.
    dirs_to_create = [
        "src",
        "tests",
        "data",
        "results",
        "data/raw",
        "data/processed",
        "state"
    ]

    root = Path(".")
    created_count = 0
    existing_count = 0

    for dir_path in dirs_to_create:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
            existing_count += 1

    print(f"Project structure initialization complete. Created: {created_count}, Existing: {existing_count}")
    return 0

if __name__ == "__main__":
    sys.exit(main())