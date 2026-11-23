"""
Module to initialize the project directory structure.
Creates required directories for code, tests, data, and results.
"""
import os
from pathlib import Path
from config import get_project_root


def initialize_project_structure() -> None:
    """
    Create the standard project directory structure:
    - code/
    - tests/
    - data/raw/
    - data/processed/
    - results/

    This function ensures all necessary directories exist for the project.
    It uses the project root defined in config.py.
    """
    project_root = get_project_root()
    
    # Define the directories to create relative to project root
    directories = [
        "code",
        "tests",
        "data/raw",
        "data/processed",
        "results"
    ]
    
    created_count = 0
    for dir_name in directories:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
        # else: Directory already exists, no action needed
    
    # Log the result
    if created_count > 0:
        print(f"Created {created_count} directories under {project_root}")
    else:
        print(f"All required directories already exist under {project_root}")


if __name__ == "__main__":
    initialize_project_structure()