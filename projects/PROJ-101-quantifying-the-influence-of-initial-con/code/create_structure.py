"""
Script to initialize the project directory structure.
Creates the required folders for code, tests, data, and state management.
"""
import os
from pathlib import Path

def main():
    """
    Creates the following directory structure relative to the project root:
    - code/
    - tests/
    - data/raw/
    - data/processed/
    - state/
    """
    root = Path(__file__).parent.parent
    
    directories = [
        "code",
        "tests",
        "data/raw",
        "data/processed",
        "state"
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"Directory structure initialization complete. Created {created_count} new directories.")
    return 0

if __name__ == "__main__":
    exit(main())
