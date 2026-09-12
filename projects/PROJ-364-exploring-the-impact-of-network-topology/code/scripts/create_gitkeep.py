"""
Script to create .gitkeep files in all project directories to ensure
version control tracking of empty directories.
"""
import os
from pathlib import Path

# Define the directories that need .gitkeep files based on T004a
# These are the directories created in the project structure
directories = [
    "data/raw",
    "data/processed",
    "results",
    "state",
    "contracts",
    "logs",
    "docs",
    "src",
    "src/data",
    "src/graphs",
    "src/metrics",
    "src/analysis",
    "src/utils",
    "src/data_ingestion",
    "src/constants",
    "tests/unit",
    "tests/integration",
    "tests/contract",
    "scripts",
]

def create_gitkeep_files():
    """Create .gitkeep files in all specified directories."""
    base_path = Path.cwd()
    created_count = 0

    for dir_name in directories:
        dir_path = base_path / dir_name
        if dir_path.exists() and dir_path.is_dir():
            gitkeep_path = dir_path / ".gitkeep"
            if not gitkeep_path.exists():
                gitkeep_path.touch()
                print(f"Created .gitkeep in {dir_path}")
                created_count += 1
            else:
                print(f".gitkeep already exists in {dir_path}")
        else:
            print(f"Warning: Directory {dir_path} does not exist. Skipping.")

    print(f"\nTotal .gitkeep files created: {created_count}")
    return created_count

if __name__ == "__main__":
    create_gitkeep_files()