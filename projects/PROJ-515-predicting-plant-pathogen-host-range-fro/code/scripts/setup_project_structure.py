import os
import sys
from pathlib import Path

def create_directories(base_path: str = None) -> None:
    """
    Initialize the project directory structure.
    
    Creates the following directories relative to base_path (or current directory):
    - src/
    - data/raw
    - data/processed
    - data/models
    - data/reports
    - logs/
    - tests/
    - contracts/
    
    Args:
        base_path: Optional base path. If None, uses current working directory.
    """
    if base_path is None:
        base_path = Path.cwd()
    else:
        base_path = Path(base_path)
    
    # Define relative directory paths
    directories = [
        "src",
        "data/raw",
        "data/processed",
        "data/models",
        "data/reports",
        "logs",
        "tests",
        "contracts"
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
    
    print(f"Project structure initialization complete. Created {created_count} new directories.")

if __name__ == "__main__":
    # Allow running as script: python setup_project_structure.py [optional_base_path]
    if len(sys.argv) > 1:
        base = sys.argv[1]
    else:
        base = None
    create_directories(base)