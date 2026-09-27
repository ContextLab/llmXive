import os
import sys
from pathlib import Path

def create_directory_structure():
    """
    Create the project root directory structure as per the implementation plan.
    
    Creates the following directories relative to the project root:
    - code/
    - data/raw/
    - data/processed/
    - data/outputs/
    - tests/
    - output/
    """
    # Define the base path (project root)
    base_path = Path.cwd()
    
    # Define the directories to create
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/outputs",
        "tests",
        "output"
    ]
    
    created_dirs = []
    for dir_name in directories:
        full_path = base_path / dir_name
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(full_path))
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")
    
    return created_dirs

def main():
    """Main entry point for the script."""
    print("Setting up project directory structure...")
    created = create_directory_structure()
    if created:
        print(f"Successfully created {len(created)} directories.")
    else:
        print("No new directories were created (all already exist).")

if __name__ == "__main__":
    main()