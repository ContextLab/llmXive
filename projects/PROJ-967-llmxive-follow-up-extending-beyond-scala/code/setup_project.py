"""
Script to initialize the project directory structure for PROJ-967.
This script creates the required directories and empty configuration files
as specified in task T001a, T001b, and T001c.

Usage:
    python code/setup_project.py
"""
import os
from pathlib import Path

def setup_directories():
    """Create the required project directory structure."""
    # Define the root project directory
    root = Path(__file__).resolve().parent.parent
    
    # Define required directories relative to root
    dirs_to_create = [
        "data/raw",
        "data/processed",
        "code",
        "tests",
        "results",
        "projects/PROJ-967-llmxive-follow-up-extending-beyond-scala"
    ]
    
    print(f"Project root identified at: {root}")
    
    for dir_path in dirs_to_create:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")
    
    return root

def create_empty_files(root: Path):
    """Create the required empty configuration files."""
    # Define files to create as empty
    files_to_create = [
        "code/requirements.txt",
        ".gitignore",
        "pytest.ini"
    ]
    
    for file_path in files_to_create:
        full_path = root / file_path
        if not full_path.exists():
            full_path.touch()
            print(f"Created empty file: {full_path}")
        else:
            print(f"File already exists: {full_path}")

def main():
    """Main entry point for project setup."""
    print("Starting project setup for PROJ-967...")
    root = setup_directories()
    create_empty_files(root)
    print("Project setup complete.")

if __name__ == "__main__":
    main()