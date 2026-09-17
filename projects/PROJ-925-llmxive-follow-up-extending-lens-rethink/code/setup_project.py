import os
import sys
from pathlib import Path
from config import get_project_root

def create_structure():
    """
    Execute structure creation for the project.
    Creates the following directories at the project root:
    - data/raw
    - data/processed
    - code
    - code/tests
    - code/utils
    - code/models
    - docs
    
    Note: data/ and code/ are SIBLING directories at the project root.
    """
    root = get_project_root()
    
    # Define the directories to create relative to the project root
    directories = [
        "data/raw",
        "data/processed",
        "code",
        "code/tests",
        "code/utils",
        "code/models",
        "docs"
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"Structure creation complete. {created_count} new directories created.")
    return created_count

def main():
    """Entry point for script execution."""
    print("Starting project structure creation...")
    create_structure()
    print("Done.")

if __name__ == "__main__":
    main()