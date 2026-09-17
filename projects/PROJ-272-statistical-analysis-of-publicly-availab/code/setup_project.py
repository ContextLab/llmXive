"""
Project structure initialization script for the llmXive statistical analysis pipeline.

This script creates the required directory structure as specified in the implementation plan.
It ensures all necessary folders for code, data, tests, and specifications exist before
any data processing or analysis begins.

Usage:
    python code/setup_project.py
"""
import os
import sys
from pathlib import Path

# Define the project root (assumed to be the parent of the code/ directory)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Directory structure to create
REQUIRED_DIRS = [
    "code",
    "data/raw",
    "data/processed",
    "data/interim",
    "data/results",
    "tests/unit",
    "tests/contract",
    "tests/integration",
    "specs/001-statistical-cognitive-decline/contracts",
]

def create_directory(dir_path: Path) -> bool:
    """
    Create a directory if it does not exist.
    
    Args:
        dir_path: Path object representing the directory to create.
        
    Returns:
        True if directory was created or already exists, False otherwise.
    """
    try:
        dir_path.mkdir(parents=True, exist_ok=True)
        return True
    except PermissionError:
        print(f"Permission denied: Unable to create directory {dir_path}")
        return False
    except Exception as e:
        print(f"Error creating directory {dir_path}: {e}")
        return False

def main():
    """Main entry point for project structure setup."""
    print(f"Initializing project structure at: {PROJECT_ROOT}")
    
    success_count = 0
    total_dirs = len(REQUIRED_DIRS)
    
    for dir_name in REQUIRED_DIRS:
        full_path = PROJECT_ROOT / dir_name
        if create_directory(full_path):
            print(f"✓ Created: {full_path.relative_to(PROJECT_ROOT)}")
            success_count += 1
        else:
            print(f"✗ Failed: {full_path.relative_to(PROJECT_ROOT)}")
    
    print(f"\nProject structure initialization complete: {success_count}/{total_dirs} directories created.")
    
    if success_count == total_dirs:
        print("All required directories are ready for use.")
        return 0
    else:
        print("Warning: Some directories could not be created. Please check permissions.")
        return 1

if __name__ == "__main__":
    sys.exit(main())