import os
import sys
from pathlib import Path

def create_directories():
    """
    Creates the project directory tree as defined in plan.md.
    
    Required directories:
    - code/
    - data/raw/
    - data/processed/
    - data/generated/
    - data/validation/
    - tests/
    
    Returns:
        bool: True if all directories were created successfully.
    """
    # Define the project root (assuming this script is in code/, so root is parent)
    # However, to be safe and explicit as per "stay inside project tree", 
    # we assume the script is run from the project root or we define root relative to this file.
    # Given the task is to create the tree, we will assume the current working directory
    # is the project root, or we derive it from the script location if needed.
    # Standard convention for these pipelines: script runs from root.
    
    root = Path.cwd()
    
    # Define the required directory structure
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/generated",
        "data/validation",
        "tests"
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
        else:
            # Ensure it is actually a directory, not a file
            if not full_path.is_dir():
                raise NotADirectoryError(f"Path exists but is not a directory: {full_path}")
    
    # Verify creation
    all_exist = all((root / d).is_dir() for d in directories)
    
    if all_exist:
        print(f"Successfully ensured {len(directories)} directories exist.")
        return True
    else:
        raise RuntimeError("Failed to create all required directories.")

if __name__ == "__main__":
    create_directories()