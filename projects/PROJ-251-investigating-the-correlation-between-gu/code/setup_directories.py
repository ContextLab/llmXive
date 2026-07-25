import os
import sys
from pathlib import Path

def create_directories():
    """
    Creates the required project directory structure for the gut microbiome study.
    
    Directories created:
    - code/
    - data/raw
    - data/processed
    - data/results
    - specs/001-investigating-the-correlation-between-gu/contracts/
    
    Returns:
        bool: True if all directories were created or already exist.
    """
    # Define the project root (assuming this script is in code/)
    # We go up one level to find the project root
    project_root = Path(__file__).resolve().parent.parent
    
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/results",
        "specs/001-investigating-the-correlation-between-gu/contracts"
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
        else:
            # Verify it is actually a directory
            if not full_path.is_dir():
                raise RuntimeError(f"Path exists but is not a directory: {full_path}")
    
    return True

if __name__ == "__main__":
    create_directories()
    print("Directory structure verified/created successfully.")
