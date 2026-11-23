"""
T001: Create project directory structure.

This script initializes the directory tree for the molecular properties prediction
project as defined in the task specification.
"""
import os
from pathlib import Path

def main():
    project_root = Path("projects/PROJ-324-predicting-molecular-properties-from-ope")
    
    # Define required subdirectories
    directories = [
        "code",
        "tests",
        "data/raw",
        "data/processed",
        "data/derived"
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created: {full_path}")
            created_count += 1
        else:
            print(f"Exists: {full_path}")
    
    # Create __init__.py files to make directories Python packages where appropriate
    # code and tests are typically packages
    (project_root / "code" / "__init__.py").touch(exist_ok=True)
    (project_root / "tests" / "__init__.py").touch(exist_ok=True)
    
    print(f"\nProject structure initialized at {project_root}")
    print(f"Created {created_count} new directories.")

if __name__ == "__main__":
    main()