"""
Setup script to create the required data directory structure for the project.
This script creates the following directories under the project root:
- data/raw
- data/processed
- artifacts/figures
- artifacts/logs
"""
import os
import sys
from pathlib import Path


def main():
    """Create the data directory structure."""
    # Determine project root (assuming script is run from project root or code/)
    # If run from code/, go up one level. If run from root, stay.
    current_path = Path(__file__).resolve()
    if current_path.name == "setup_data_dirs.py":
        project_root = current_path.parent
    else:
        project_root = current_path.parent.parent

    # Define the directories to create relative to project root
    dirs_to_create = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "artifacts" / "figures",
        project_root / "artifacts" / "logs",
    ]

    created_count = 0
    for dir_path in dirs_to_create:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")

    print(f"Setup complete. {created_count} new directories created.")
    return 0


if __name__ == "__main__":
    sys.exit(main())