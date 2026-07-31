"""
Script to initialize the project directory structure for PROJ-037.
This script creates the required folder hierarchy and placeholder files
as defined in task T001a and T001b.
"""
import os
from pathlib import Path

def main():
    # Define the project root based on the task requirement
    # The task specifies: projects/PROJ-037-investigating-the-correlation-between-gu/
    project_root = Path("projects/PROJ-037-investigating-the-correlation-between-gu")
    
    # Define required subdirectories
    directories = [
        "data/raw",
        "data/processed",
        "data/outputs",
        "code",
        "tests",
        "docs"
    ]
    
    # Create directories
    for dir_path in directories:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")
    
    # Create placeholder files as per T001b
    # These must exist in the project root
    placeholder_files = [
        "README.md",
        ".gitignore",
        "requirements.txt"
    ]
    
    for file_name in placeholder_files:
        file_path = project_root / file_name
        # Create empty file if it doesn't exist
        if not file_path.exists():
            file_path.touch()
            print(f"Created empty file: {file_path}")
        else:
            print(f"File already exists: {file_path}")
    
    # Verify structure
    print("\nVerification:")
    for dir_path in directories:
        full_path = project_root / dir_path
        if full_path.is_dir():
            print(f"  [OK] {full_path}")
        else:
            print(f"  [FAIL] {full_path} is missing")
    
    for file_name in placeholder_files:
        file_path = project_root / file_name
        if file_path.is_file():
            print(f"  [OK] {file_path}")
        else:
            print(f"  [FAIL] {file_path} is missing")

if __name__ == "__main__":
    main()