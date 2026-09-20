import os
import sys
from pathlib import Path
from typing import List, Tuple
from setup_project import ensure_directory, create_gitkeep, setup_directories, main

def setup_directories() -> None:
    """
    Setup the specific directory structure for T008:
    data/raw/, data/processed/, and results/ with .gitkeep files.
    This function is called by the main entry point in this file.
    """
    # Define the project root based on the project structure
    # Assuming the script runs from the project root or code/ directory
    project_root = Path(__file__).resolve().parent.parent
    
    # Define the relative paths to create
    directories_to_create = [
        "data/raw",
        "data/processed",
        "results"
    ]
    
    created_paths: List[Path] = []
    
    for dir_name in directories_to_create:
        full_path = project_root / dir_name
        if ensure_directory(full_path):
            created_paths.append(full_path)
            create_gitkeep(full_path)
            print(f"Created directory with .gitkeep: {full_path}")
        else:
            print(f"Directory already exists or could not be created: {full_path}")
    
    return created_paths

def main() -> None:
    """
    Main entry point for T008 implementation.
    Sets up the required directory structure.
    """
    print("Starting T008: Setup data and results directories...")
    try:
        paths = setup_directories()
        print(f"Successfully created {len(paths)} directories.")
    except Exception as e:
        print(f"Error during directory setup: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
