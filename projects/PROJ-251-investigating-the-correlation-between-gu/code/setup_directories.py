"""
Setup script to create the required project directory structure.
Creates: code/, data/raw, data/processed, data/results,
         specs/001-investigating-the-correlation-between-gu/contracts/
"""
import os
import sys
from pathlib import Path


def create_directories():
    """Create all required project directories."""
    # Define the base directory (project root)
    base_dir = Path(__file__).resolve().parent.parent

    # Define the directories to create relative to the project root
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/results",
        "specs/001-investigating-the-correlation-between-gu/contracts",
    ]

    created_count = 0
    skipped_count = 0

    for dir_path in directories:
        full_path = base_dir / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            if full_path.exists():
                print(f"Directory created/verified: {full_path}")
                created_count += 1
            else:
                print(f"Error: Failed to create {full_path}")
        except OSError as e:
            print(f"Error creating directory {full_path}: {e}")

    print(f"\nSummary: {created_count} directories created/verified, {skipped_count} skipped.")
    return created_count == len(directories)


if __name__ == "__main__":
    success = create_directories()
    sys.exit(0 if success else 1)
