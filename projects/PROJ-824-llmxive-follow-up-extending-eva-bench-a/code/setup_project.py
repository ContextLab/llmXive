import os
from pathlib import Path

def create_project_structure():
    """
    Creates the required directory structure for the project.
    
    Directories created:
    - data/raw/
    - data/processed/
    - code/
    - tests/
    - specs/
    """
    base_path = Path(".")
    
    directories = [
        base_path / "data" / "raw",
        base_path / "data" / "processed",
        base_path / "code",
        base_path / "tests",
        base_path / "specs",
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")
    
    return True

if __name__ == "__main__":
    create_project_structure()