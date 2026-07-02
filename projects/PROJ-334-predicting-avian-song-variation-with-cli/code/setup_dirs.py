"""
Script to execute directory structure creation for the avian song variation project.
Implements Task T001b: Execute directory structure script.

This script uses the `create_project_structure` and `get_project_paths` functions
from `code/utils.py` to ensure consistency with the project's utility definitions.
"""
import os
import sys
from pathlib import Path

# Ensure the project root is in the path to import utils
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils import create_project_structure, get_project_paths


def main():
    """
    Executes the directory structure creation based on the project plan.
    """
    print("Initializing directory structure for PROJ-334-predicting-avian-song-variation...")
    
    # Retrieve the standard paths defined in the project utilities
    paths = get_project_paths()
    
    # Create the directory structure
    # The create_project_structure function handles the actual creation logic
    # and ensures all necessary subdirectories (raw, processed, etc.) are made.
    created_count = create_project_structure(paths)
    
    if created_count > 0:
        print(f"Successfully created {created_count} directories.")
        print("Directory structure ready.")
    else:
        print("No new directories were created (structure may already exist).")

    # Verify specific required paths exist as per task requirements
    required_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "output",
        "tests"
    ]
    
    missing = []
    for rel_path in required_dirs:
        full_path = project_root / rel_path
        if not full_path.exists() or not full_path.is_dir():
            missing.append(rel_path)
    
    if missing:
        print(f"ERROR: The following required directories are missing: {missing}")
        sys.exit(1)
    
    print("Verification complete: All required directories exist.")


if __name__ == "__main__":
    main()
