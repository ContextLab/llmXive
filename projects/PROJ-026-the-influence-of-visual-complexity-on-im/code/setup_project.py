import os
from pathlib import Path
from config import get_project_root

def create_directories():
    """
    Creates the required directory structure for the project.
    
    Directories created:
    - data/raw/stimuli
    - data/raw/responses
    - data/processed
    - data/results
    """
    root = get_project_root()
    
    # Define the relative paths to create
    dirs_to_create = [
        "data/raw/stimuli",
        "data/raw/responses",
        "data/processed",
        "data/results"
    ]
    
    for dir_path in dirs_to_create:
        full_path = root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")

if __name__ == "__main__":
    create_directories()