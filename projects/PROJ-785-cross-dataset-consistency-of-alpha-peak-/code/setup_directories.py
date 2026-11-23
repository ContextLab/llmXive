import os
import sys
from pathlib import Path

from config import get_project_root, ensure_directories_exist


def create_directories() -> None:
    """
    Creates the required directory structure for the project.
    
    This function ensures the existence of the following directories relative 
    to the project root:
    - code/
    - tests/
    - data/raw
    - data/derivatives
    - data/processed
    - state/
    
    This satisfies task T001a: Create directory structure.
    """
    project_root = get_project_root()
    
    # Define the required directory paths relative to the project root
    required_dirs = [
        "code",
        "tests",
        "data/raw",
        "data/derivatives",
        "data/processed",
        "state",
        # Additional subdirectories often needed for organization
        "data/derivatives/preprocessed",
        "data/processed/estimates",
        "data/processed/reports",
        "state/logs",
    ]
    
    # Create the directories using the existing ensure_directories_exist helper
    ensure_directories_exist(project_root, required_dirs)
    
    print(f"Directory structure created successfully under: {project_root}")
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        if dir_path.exists():
            print(f"  [OK] {dir_path}")
        else:
            # This should not happen if ensure_directories_exist works correctly
            print(f"  [FAIL] {dir_path} was not created.")
            sys.exit(1)


if __name__ == "__main__":
    create_directories()