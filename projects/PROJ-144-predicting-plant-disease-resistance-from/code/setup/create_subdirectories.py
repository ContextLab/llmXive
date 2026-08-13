"""
Task T001b: Create sub-directories for the project data and results structure.

Creates the following directories:
- data/raw
- data/processed
- data/intermediate
- results/plots
"""
import os
import sys
from pathlib import Path

# Define the project root (assuming script is run from root or code/setup)
# We look for a 'data' or 'results' folder to anchor, otherwise assume current dir
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

def create_subdirectories():
    """Create the required sub-directories."""
    dirs_to_create = [
        PROJECT_ROOT / "data" / "raw",
        PROJECT_ROOT / "data" / "processed",
        PROJECT_ROOT / "data" / "intermediate",
        PROJECT_ROOT / "results" / "plots",
    ]

    created_count = 0
    for dir_path in dirs_to_create:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")
    
    print(f"Total directories created/verified: {len(dirs_to_create)}")
    return True

def main():
    """Entry point for the script."""
    try:
        success = create_subdirectories()
        if success:
            print("T001b: Sub-directories successfully created.")
            sys.exit(0)
        else:
            print("T001b: Failed to create sub-directories.")
            sys.exit(1)
    except Exception as e:
        print(f"Error during directory creation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
