import os
import sys
from pathlib import Path

def create_directories():
    """
    Creates the required project directory structure as specified in T001.
    Directories created:
    - code/
    - data/raw/
    - data/processed/
    - data/reports/
    - tests/
    - state/
    """
    base_path = Path(__file__).resolve().parent.parent
    
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/reports",
        "tests",
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
    
    print(f"Project structure setup complete. {created_count} new directories created.")
    return True

if __name__ == "__main__":
    create_directories()