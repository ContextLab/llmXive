"""
Setup script to create the project directory structure for PROJ-037.
This script creates the required folders under the project root.
"""
import os
from pathlib import Path

def create_project_structure():
    # Define the base project directory
    base_dir = Path("projects/PROJ-037-investigating-the-correlation-between-gu")
    
    # Define subdirectories to create
    subdirs = [
        "data/raw",
        "data/processed",
        "data/outputs",
        "code",
        "tests",
        "docs"
    ]
    
    # Create the base directory
    base_dir.mkdir(parents=True, exist_ok=True)
    print(f"Created base directory: {base_dir}")
    
    # Create subdirectories
    created_dirs = []
    for subdir in subdirs:
        full_path = base_dir / subdir
        full_path.mkdir(parents=True, exist_ok=True)
        created_dirs.append(full_path)
        print(f"Created directory: {full_path}")
    
    # Create __init__.py files to make directories proper Python packages
    # for code and tests
    (base_dir / "code" / "__init__.py").touch()
    (base_dir / "tests" / "__init__.py").touch()
    print("Created __init__.py files in code/ and tests/")
    
    print(f"\nProject structure successfully created at: {base_dir}")
    return base_dir

if __name__ == "__main__":
    create_project_structure()