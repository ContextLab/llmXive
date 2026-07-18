"""
Setup script to create the required directory structure for the project.
This script ensures that all necessary data directories exist before execution.
"""
import os
import sys
from pathlib import Path

def create_directory(path: Path) -> None:
    """
    Create a directory if it does not exist.
    
    Args:
        path: The Path object representing the directory to create.
    """
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {path}")
    else:
        print(f"Directory already exists: {path}")

def main() -> None:
    """
    Main function to set up the project directory structure.
    Creates the following directories:
    - data/raw
    - data/processed
    - data/synthetic
    - data/derivation_logs
    """
    # Define the base project directory (assuming code/setup_directories.py is at code/setup_directories.py)
    # We need to go up one level to get to the project root if this file is in code/
    # However, the task specifies paths relative to project root.
    # Let's assume the script is run from the project root or we determine the root dynamically.
    
    # Determine project root: assume this file is at <root>/code/setup_directories.py
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent
    
    data_dirs = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "synthetic",
        project_root / "data" / "derivation_logs",
    ]
    
    print(f"Setting up directories relative to project root: {project_root}")
    
    for dir_path in data_dirs:
        create_directory(dir_path)
    
    print("Directory setup complete.")

if __name__ == "__main__":
    main()