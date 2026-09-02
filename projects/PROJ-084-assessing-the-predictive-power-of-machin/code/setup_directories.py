"""
Setup script to create the required project directory structure.
This script creates: code/, data/raw/, data/processed/, data/results/, tests/
"""
import os
from pathlib import Path

def main():
    """Create all required project directories."""
    # Define the base project root (current working directory or specified path)
    # Assuming the script is run from the project root
    base_path = Path(".")

    # Define the directories to create relative to the project root
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/results",
        "tests"
    ]

    created_count = 0
    for dir_name in directories:
        dir_path = base_path / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")

    print(f"Setup complete. {created_count} new directories created.")
    return 0

if __name__ == "__main__":
    exit(main())