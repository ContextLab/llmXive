import os
import sys
from pathlib import Path

def setup_directories():
    """
    Create the required directory structure for the llmXive project.
    
    Creates the following directories relative to the project root:
    - data/raw
    - data/processed
    - data/interim
    - data/results
    - code (already exists, but ensures it's present)
    - tests (already exists, but ensures it's present)
    - figures
    - state
    
    Returns:
        Path: The project root path.
    """
    # Determine project root (assuming this script is in code/)
    # We go up one level from code/ to get the project root
    project_root = Path(__file__).resolve().parent.parent
    
    directories = [
        "data/raw",
        "data/processed",
        "data/interim",
        "data/results",
        "figures",
        "state",
        # code/ and tests/ are expected to exist, but we ensure them too
        "code",
        "tests",
    ]
    
    for dir_path in directories:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created/Verified: {full_path}")
    
    print(f"Directory setup complete for project at: {project_root}")
    return project_root

if __name__ == "__main__":
    setup_directories()