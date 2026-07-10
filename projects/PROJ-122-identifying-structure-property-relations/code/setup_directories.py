"""
Script to create the required directory structure for the llmXive project.
This script ensures all necessary folders for code, data, tests, and state exist.
"""
import os
from pathlib import Path

# Define the project root relative to this script's location (assuming script is in code/)
# However, tasks.md implies this script might be run from root or code/.
# We will assume the script is run from the project root to create relative paths.
# If run from code/, we need to adjust. Let's assume standard execution from root.

def create_directories():
    """Create the project directory structure."""
    base_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "data/features",
        "tests",
        "state/projects"
    ]

    created_count = 0
    skipped_count = 0

    for dir_path in base_dirs:
        path = Path(dir_path)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {path}")
            created_count += 1
        else:
            skipped_count += 1
            print(f"Directory already exists: {path}")

    print(f"\nSummary: {created_count} directories created, {skipped_count} already existed.")
    return created_count, skipped_count

if __name__ == "__main__":
    create_directories()
