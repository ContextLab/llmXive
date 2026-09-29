import os
from pathlib import Path

def create_project_structure():
    """
    Creates the project directory structure as defined in plan.md.
    This includes root directories and their subdirectories.
    
    Directories created:
    - code/ (with utils, ingestion, processing, analysis, tests subdirs)
    - data/ (with raw, processed subdirs)
    - outputs/ (with figures, reports subdirs)
    - docs/
    - state/
    """
    # Define the project root (assumed to be the parent of this file's directory)
    # However, typically scripts are run from the project root, so we create relative to cwd
    root = Path.cwd()
    
    # Define the directory tree to create
    # Based on standard conventions and the task description
    directories = [
        "code",
        "code/utils",
        "code/ingestion",
        "code/processing",
        "code/analysis",
        "code/tests",
        "data",
        "data/raw",
        "data/processed",
        "data/millennium",
        "outputs",
        "outputs/figures",
        "outputs/reports",
        "docs",
        "state"
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {full_path}")
        else:
            # Ensure it is actually a directory
            if not full_path.is_dir():
                raise NotADirectoryError(f"Path exists but is not a directory: {full_path}")
    
    print(f"Project structure ready. {created_count} new directories created.")
    return True

if __name__ == "__main__":
    create_project_structure()
