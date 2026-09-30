import os
import sys
from pathlib import Path

def create_directory_structure():
    """
    Creates the required project directory structure:
    - code/
    - data/raw/
    - data/processed/
    - data/outputs/
    - tests/
    
    Returns a list of created directory paths.
    """
    root = Path.cwd()
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/outputs",
        "tests",
        "tests/unit",
        "tests/contract",
        "specs",
        "config",
    ]
    
    created = []
    for dir_name in directories:
        full_path = root / dir_name
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created.append(str(full_path))
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")
    
    return created

def main():
    """Entry point for project structure setup."""
    print("Setting up project directory structure...")
    dirs = create_directory_structure()
    print(f"Successfully created {len(dirs)} directories.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
