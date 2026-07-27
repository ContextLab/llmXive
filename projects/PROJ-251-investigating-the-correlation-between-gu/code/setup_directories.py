import os
import sys
from pathlib import Path

def create_directories():
    """
    Creates the required project directory structure for PROJ-251.
    
    Directories created:
    - code/
    - data/raw
    - data/processed
    - data/results
    - specs/001-investigating-the-correlation-between-gu/contracts/
    """
    base_path = Path(__file__).resolve().parent.parent
    
    directories = [
        base_path / "code",
        base_path / "data" / "raw",
        base_path / "data" / "processed",
        base_path / "data" / "results",
        base_path / "specs" / "001-investigating-the-correlation-between-gu" / "contracts"
    ]
    
    created_count = 0
    for dir_path in directories:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")
    
    print(f"Directory setup complete. {created_count} new directories created.")
    return True

if __name__ == "__main__":
    create_directories()
