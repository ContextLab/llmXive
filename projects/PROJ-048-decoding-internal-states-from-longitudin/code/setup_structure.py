"""
Script to establish the project directory structure.
This script creates the necessary folders for the llmXive project.
"""
import os
from pathlib import Path

def create_directories():
    """Create the project directory tree."""
    # Define the base project root (current directory)
    base = Path(".")

    # Define the required directories relative to the base
    dirs = [
        "code/data",
        "code/analysis",
        "code/utils",
        "code/tests",
        "specs/001-decoding-internal-states/contracts",
    ]

    created_count = 0
    for dir_path in dirs:
        full_path = base / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created: {full_path}")
            created_count += 1
        else:
            print(f"Exists: {full_path}")

    print(f"\nDirectory setup complete. Created {created_count} new directories.")
    return created_count

if __name__ == "__main__":
    create_directories()