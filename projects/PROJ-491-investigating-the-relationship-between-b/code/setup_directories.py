"""
Module to create the project directory structure.
Implements T001a: Create directory structure.
"""
import os
import sys
from pathlib import Path
from config import ensure_directories

def create_directories():
    """
    Creates the required directory structure for the project:
    - code/
    - tests/
    - data/raw/
    - data/processed/
    - state/
    """
    base_path = Path(__file__).resolve().parent.parent
    
    directories = [
        "code",
        "tests",
        "data/raw",
        "data/processed",
        "state"
    ]
    
    created_count = 0
    for dir_name in directories:
        dir_path = base_path / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")
    
    # Ensure __init__.py files exist in code and tests to make them packages
    # (Though not strictly required by T001a, it's good practice for Python projects)
    for dir_name in ["code", "tests"]:
        init_path = base_path / dir_name / "__init__.py"
        if not init_path.exists():
            init_path.touch()
            print(f"Created package init: {init_path}")
    
    return created_count

def main():
    """Entry point for script execution."""
    print("Initializing project directory structure...")
    created = create_directories()
    print(f"Directory initialization complete. Created {created} new directories.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
