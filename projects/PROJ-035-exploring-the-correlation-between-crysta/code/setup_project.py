import os
import sys
from pathlib import Path

def setup_project_structure():
    """
    Creates the exact directory tree required for the project.
    Directories: src/, tests/, data/raw/, data/cleaned/, data/results/, figures/, contracts/
    """
    # Define the project root (assuming this script is at code/setup_project.py)
    # We want to create the structure relative to the repository root.
    # If running from code/, we go up one level.
    current_path = Path(__file__).resolve()
    project_root = current_path.parent.parent

    directories = [
        "src",
        "tests",
        "data/raw",
        "data/cleaned",
        "data/results",
        "figures",
        "contracts"
    ]

    created_count = 0
    for dir_name in directories:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")

    if created_count == 0:
        print("All required directories already exist.")
    else:
        print(f"Successfully created {created_count} new directories.")

    return True

def main():
    """Entry point for CLI execution."""
    success = setup_project_structure()
    if success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
