import os
from pathlib import Path

def create_directories():
    """
    Creates the required directory structure for the project.
    Ensures data/raw, data/derived, and docs/output directories exist.
    """
    project_root = Path(__file__).resolve().parent.parent
    
    # Define directories to create based on task requirements
    directories = [
        project_root / "data" / "raw",
        project_root / "data" / "derived",
        project_root / "docs" / "output",
    ]
    
    for dir_path in directories:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")

if __name__ == "__main__":
    create_directories()