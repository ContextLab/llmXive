"""
Setup script to initialize the project directory structure for the corrosion potential prediction pipeline.
This script creates the required directories as specified in T001.
"""
import os
from pathlib import Path

def create_directories():
    """Create the required project directory structure."""
    # Define the base directories relative to the project root
    base_dirs = [
        "code",
        "data",
        "state",
        "contracts",
        "config",
    ]

    # Define the subdirectories
    sub_dirs = [
        "data/raw",
        "data/processed",
        "data/logs",
        "code/data",
        "code/models",
        "code/utils",
        "code/tests",
    ]

    # Combine base and sub directories
    all_dirs = base_dirs + sub_dirs

    # Create the directories
    created_count = 0
    for dir_path in all_dirs:
        path = Path(dir_path)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {path}")
            created_count += 1
        else:
            print(f"Directory already exists: {path}")

    print(f"\nTotal directories created in this run: {created_count}")
    print("Project directory structure initialization complete.")

if __name__ == "__main__":
    create_directories()
