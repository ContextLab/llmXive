import os
import sys
from pathlib import Path

def create_structure():
    """
    Creates the required project directory structure for PROJ-755.
    
    Directories created:
    - data/raw
    - data/processed
    - code
    - code/utils
    - tests
    - tests/contract
    - tests/unit
    - tests/integration
    - docs
    - state
    """
    project_root = Path.cwd()
    
    directories = [
        "data/raw",
        "data/processed",
        "code",
        "code/utils",
        "tests",
        "tests/contract",
        "tests/unit",
        "tests/integration",
        "docs",
        "state",
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"\nProject structure setup complete. Created {created_count} new directories.")
    return created_count

def main():
    """Entry point for the script."""
    create_structure()

if __name__ == "__main__":
    main()
