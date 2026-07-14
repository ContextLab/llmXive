"""
Script to initialize the project directory structure for PROJ-077.
Creates the required directories: data/raw, data/processed, code, and tests.
"""
import os
from pathlib import Path
from config import ensure_directories

def main():
    """Create the project directory structure."""
    # Define the base project path
    base_path = Path("projects/PROJ-077-investigating-the-correlation-between-gu")
    
    # Define the required subdirectories relative to the base path
    required_dirs = [
        "data/raw",
        "data/processed",
        "code",
        "tests"
    ]
    
    # Create the base directory if it doesn't exist
    base_path.mkdir(parents=True, exist_ok=True)
    print(f"Base project directory ensured: {base_path}")
    
    # Create each required subdirectory
    for dir_name in required_dirs:
        full_path = base_path / dir_name
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")
    
    # Verify all directories exist
    all_exist = True
    for dir_name in required_dirs:
        full_path = base_path / dir_name
        if not full_path.is_dir():
            print(f"ERROR: Directory {full_path} was not created.")
            all_exist = False
    
    if all_exist:
        print("\nProject structure initialization complete.")
        print(f"Directories created under {base_path}:")
        for dir_name in required_dirs:
            print(f"  - {dir_name}")
    else:
        print("\nERROR: Some directories failed to create.")
        return 1
        
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())