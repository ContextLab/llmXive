import os
from pathlib import Path
import sys

def main():
    """
    Create the foundational directory structure for the llmXive project.
    This script ensures that src/, tests/, data/, and specs/ directories
    exist at the project root relative to the script location.
    """
    # Determine the project root (parent of the 'code' directory where this script lives)
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent

    # Define the required top-level directories
    required_dirs = [
        "src",
        "tests",
        "data",
        "specs"
    ]

    created_count = 0
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")

    # Also create the specific subdirectories required by T001b and T001c
    # as part of this single setup script to ensure full compliance with Phase 1.
    subdirectories = [
        "data/raw",
        "data/processed",
        "data/interim",
        "src/data",
        "src/features",
        "src/models",
        "src/utils"
    ]

    for sub_dir in subdirectories:
        dir_path = project_root / sub_dir
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created subdirectory: {dir_path}")
            created_count += 1
        else:
            print(f"Subdirectory already exists: {dir_path}")

    print(f"Setup complete. {created_count} directories ensured.")

if __name__ == "__main__":
    main()