"""
Directory setup module for the cosmological principle assessment pipeline.
Creates the required project directory structure.
"""
import os
import sys
from pathlib import Path


def create_directories():
    """
    Creates the required project directories if they do not already exist.
    
    Creates:
        - code/
        - tests/
        - data/raw/
        - data/processed/
        - data/simulations/
        - data/reports/
        - docs/
        
    Returns:
        list: A list of absolute paths (as strings) of the created directories.
        
    Raises:
        OSError: If a directory cannot be created due to permissions or other OS errors.
    """
    # Define relative paths based on the project root
    relative_paths = [
        "code",
        "tests",
        "data/raw",
        "data/processed",
        "data/simulations",
        "data/reports",
        "docs"
    ]
    
    # Determine the project root. 
    # If this file is run as a script, __file__ is relative to the script location.
    # We assume the project root is the parent of the 'code' directory.
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent
    
    created_dirs = []
    
    for rel_path in relative_paths:
        full_path = project_root / rel_path
        
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")
        
        created_dirs.append(str(full_path))
        
    return created_dirs


if __name__ == "__main__":
    # Execute directory creation when run directly
    dirs = create_directories()
    print(f"Project structure ready. Directories: {dirs}")
