"""
Setup script for PROJ-175: Statistical Analysis of Publicly Available Recipe Data.
Creates the required directory structure and initial placeholder files.
"""
import os
from pathlib import Path

# Define the project root relative to where this script is run
# Assuming the script is run from the repository root
PROJECT_ROOT = Path("projects/PROJ-175-statistical-analysis-of-publicly-availab")

# Directories to create
DIRECTORIES = [
    PROJECT_ROOT / "code",
    PROJECT_ROOT / "data",
    PROJECT_ROOT / "data" / "raw",
    PROJECT_ROOT / "data" / "processed",
    PROJECT_ROOT / "data" / "final",
    PROJECT_ROOT / "tests",
]

# Files to create (empty)
FILES = [
    PROJECT_ROOT / "code" / "__init__.py",
    PROJECT_ROOT / "tests" / "__init__.py",
    PROJECT_ROOT / "code" / "data" / "__init__.py",
    PROJECT_ROOT / "code" / "requirements.txt",
    PROJECT_ROOT / "tests" / "conftest.py",
]

def main():
    print(f"Setting up project structure at: {PROJECT_ROOT}")
    
    # Create directories
    for dir_path in DIRECTORIES:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")
    
    # Create empty files
    for file_path in FILES:
        # Ensure parent directory exists (for nested files like code/data/__init__.py)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        if not file_path.exists():
            file_path.touch()
            print(f"Created empty file: {file_path}")
        else:
            print(f"File already exists: {file_path}")

    print("Project setup complete.")

if __name__ == "__main__":
    main()
