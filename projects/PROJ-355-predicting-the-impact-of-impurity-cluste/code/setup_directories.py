import os
import sys
from pathlib import Path
from setup_project import ensure_directory, create_gitkeep

def setup_directories():
    """
    Setup the required directory structure for the project:
    - data/raw/
    - data/processed/
    - results/
    
    Creates .gitkeep files in each directory to ensure they are tracked by git.
    """
    # Define the relative paths to create
    directories = [
        "data/raw",
        "data/processed",
        "results"
    ]
    
    project_root = Path(__file__).resolve().parent.parent
    
    for dir_path in directories:
        full_path = project_root / dir_path
        ensure_directory(full_path)
        create_gitkeep(full_path)
        print(f"Created directory: {full_path} with .gitkeep")

def main():
    """Entry point for the script."""
    setup_directories()
    print("Directory structure setup complete.")

if __name__ == "__main__":
    main()