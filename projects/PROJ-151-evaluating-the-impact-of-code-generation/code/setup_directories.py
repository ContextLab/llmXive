import os
import sys
from pathlib import Path

def create_directories() -> None:
    """
    Create the project directory tree as defined in plan.md.
    
    Required directories:
    - code/
    - data/raw/
    - data/processed/
    - data/generated/
    - data/validation/
    - tests/
    
    This function ensures the root directories and subdirectories exist
    before any data ingestion or generation scripts are run.
    """
    project_root = Path(__file__).resolve().parent.parent
    
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/generated",
        "data/validation",
        "tests",
    ]
    
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")

    # Verify creation
    missing = [d for d in directories if not (project_root / d).exists()]
    if missing:
        raise RuntimeError(f"Failed to create directories: {missing}")

    print("Project directory tree successfully created.")

if __name__ == "__main__":
    create_directories()
