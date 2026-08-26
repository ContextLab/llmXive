import os
import sys
from pathlib import Path

def create_directories():
    """
    Create the required project directory structure explicitly.
    Directories created:
      - code/
      - data/raw
      - data/processed
      - data/results
      - specs/001-investigating-the-correlation-between-gu/contracts/
    """
    # Define the project root (assuming this script is run from the root or code/)
    # We use the directory of this script as the base if run as main, 
    # otherwise we assume current working directory is project root.
    # To be safe, we resolve relative to the current working directory.
    project_root = Path.cwd()

    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/results",
        "data/research", # Added based on T010 output requirement
        "specs/001-investigating-the-correlation-between-gu/contracts",
    ]

    created_count = 0
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")

    return created_count

def main():
    """Main entry point for directory creation."""
    print("Starting directory creation for project...")
    count = create_directories()
    print(f"Finished. {count} new directories created.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
