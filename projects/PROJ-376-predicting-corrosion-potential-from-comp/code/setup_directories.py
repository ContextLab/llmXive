"""
Project Directory Initialization Script.

Creates the required directory structure for the corrosion potential prediction pipeline.
Ensures all necessary folders for data, code, models, logs, and configuration exist.
"""
import os
from pathlib import Path


def create_directories():
    """
    Create the full project directory structure as defined in T001.
    
    Creates the following directories relative to the project root:
    - code/
    - data/
    - data/raw/
    - data/processed/
    - data/logs/
    - state/
    - contracts/
    - config/
    - code/data/
    - code/models/
    - code/utils/
    - code/tests/
    """
    # Define the base project root (assumed to be the current working directory
    # or the directory containing this script if run as __main__)
    project_root = Path(__file__).resolve().parent.parent
    
    directories = [
        "code",
        "data",
        "data/raw",
        "data/processed",
        "data/logs",
        "state",
        "contracts",
        "config",
        "code/data",
        "code/models",
        "code/utils",
        "code/tests",
    ]
    
    created_count = 0
    
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {full_path.relative_to(project_root)}")
        else:
            print(f"Directory already exists: {full_path.relative_to(project_root)}")
    
    print(f"\nDirectory setup complete. {created_count} new directories created.")
    return created_count


if __name__ == "__main__":
    create_directories()
