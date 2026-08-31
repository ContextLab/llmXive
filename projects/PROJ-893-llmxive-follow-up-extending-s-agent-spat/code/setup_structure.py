import os
import sys
from pathlib import Path

def create_directories():
    """
    Creates the project directory structure as defined in plan.md.
    Directories created:
    - code/
    - data/raw/
    - data/derived/
    - data/results/
    - specs/
    - tests/
    """
    base_path = Path(__file__).resolve().parent.parent
    
    directories = [
        "code",
        "data/raw",
        "data/derived",
        "data/results",
        "specs",
        "tests"
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
    
    print(f"Project structure initialization complete. {created_count} new directories created.")
    return True

if __name__ == "__main__":
    success = create_directories()
    sys.exit(0 if success else 1)