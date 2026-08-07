import os
import sys
from pathlib import Path
from typing import List

def create_directories() -> bool:
    """
    Creates the required project directory structure.
    Returns True if all directories were created or already exist.
    Returns False if any directory creation failed.
    """
    base_path = Path(__file__).resolve().parent.parent
    directories = [
        "code",
        "data/raw",
        "data/curated",
        "data/results",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "specs/001-llmxive-follow-up-extending-swe-explore/contracts",
        "state",
        "docs",
        "figures",
        "paper"
    ]

    success = True
    for dir_name in directories:
        full_path = base_path / dir_name
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            if full_path.is_dir():
                print(f"Directory created/exists: {full_path}")
            else:
                print(f"ERROR: Failed to create directory: {full_path}")
                success = False
        except OSError as e:
            print(f"ERROR: OSError while creating {full_path}: {e}")
            success = False

    return success

def main():
    print("Creating project structure for llmXive follow-up...")
    if create_directories():
        print("Project structure created successfully.")
        return 0
    else:
        print("Project structure creation failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
