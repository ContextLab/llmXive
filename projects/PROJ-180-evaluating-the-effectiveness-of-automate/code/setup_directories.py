"""
Script to initialize the project directory structure.
Creates code/, data/raw, data/processed, results/, and specs/ directories.
"""
import os
import sys
from pathlib import Path

def main():
    """Create the required project directory structure."""
    # Define the root directory (current working directory)
    root = Path.cwd()

    # Define the directories to create based on tasks.md T001a
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "results",
        "specs"
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

    print(f"Setup complete. {created_count} new directories created.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
