"""
Project Structure Setup Script for llmXive - Predicting Molecular Descriptors.

This script initializes the required directory structure for the project,
ensuring all necessary folders exist for code, data (raw, processed, results),
tests, and utilities.
"""
import os
import sys
from pathlib import Path

# Define the project root relative to this script or current working directory
# Assuming this script is run from the project root
PROJECT_ROOT = Path.cwd()

# Required directory structure as per T001
REQUIRED_DIRS = [
    "code",
    "data/raw",
    "data/processed",
    "data/results",
    "tests",
    "utils"
]

def create_directory(dir_path: Path) -> bool:
    """
    Creates a directory if it does not exist.
    
    Args:
        dir_path: Path object representing the directory to create.
        
    Returns:
        True if directory was created or already exists, False on error.
    """
    try:
        dir_path.mkdir(parents=True, exist_ok=True)
        # Create a .gitkeep file to ensure the directory is tracked by git
        # even if it's empty, which is a common practice for data directories.
        gitkeep_file = dir_path / ".gitkeep"
        if not gitkeep_file.exists():
            gitkeep_file.touch()
        print(f"Directory created/verified: {dir_path}")
        return True
    except Exception as e:
        print(f"Error creating directory {dir_path}: {e}")
        return False

def main():
    """
    Main entry point to initialize the project structure.
    """
    print(f"Initializing project structure at: {PROJECT_ROOT}")
    
    success = True
    for dir_name in REQUIRED_DIRS:
        full_path = PROJECT_ROOT / dir_name
        if not create_directory(full_path):
            success = False
    
    if success:
        print("\nProject structure initialization complete.")
        print("Directories created:")
        for dir_name in REQUIRED_DIRS:
            print(f"  - {dir_name}/")
    else:
        print("\nProject structure initialization failed due to errors.")
        sys.exit(1)

if __name__ == "__main__":
    main()