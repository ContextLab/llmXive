"""
setup_directories.py

Creates the project directory structure as defined in T001.
"""
import os
import sys

def create_project_structure():
    """Creates the required directories for the project."""
    directories = [
        "data/raw",
        "data/results",
        "code",
        "tests/unit",
        "tests/contract",
        "contracts",
        "figures",
        "state"
    ]
    
    created = []
    for dir_path in directories:
        os.makedirs(dir_path, exist_ok=True)
        created.append(dir_path)
        print(f"Created directory: {dir_path}")
        
    return created

def main():
    print("Setting up project directories...")
    dirs = create_project_structure()
    print(f"Successfully created {len(dirs)} directories.")

if __name__ == "__main__":
    main()
