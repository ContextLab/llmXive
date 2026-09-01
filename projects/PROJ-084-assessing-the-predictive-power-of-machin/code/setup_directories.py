"""
Script to initialize the project directory structure.
Creates code/, data/raw/, data/processed/, data/results/, and tests/ directories.
"""
import os
from pathlib import Path

def main():
    """Create the required project directories."""
    # Define the project root (current directory)
    root = Path(".")

    # Define the directories to create relative to the root
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/results",
        "tests"
    ]

    created_count = 0
    for dir_name in directories:
        target_path = root / dir_name
        if not target_path.exists():
            target_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {target_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {target_path}")

    print(f"Directory setup complete. {created_count} new directories created.")

if __name__ == "__main__":
    main()
