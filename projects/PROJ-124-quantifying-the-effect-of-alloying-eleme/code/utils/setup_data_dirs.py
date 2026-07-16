"""
Utility module for creating the required data directory structure.

This module implements Task T004a: Create `data/raw/` and `data/processed/` 
directory structure. It ensures that the necessary directories for the 
pipeline exist before data ingestion and processing tasks run.
"""
import os
from pathlib import Path
import sys

def create_data_directories(base_path: str = ".") -> bool:
    """
    Create the required data directory structure.
    
    Args:
        base_path: The root directory where the data folders will be created.
                   Defaults to current working directory.
    
    Returns:
        True if all directories were created successfully, False otherwise.
    """
    base = Path(base_path)
    
    # Define required directories relative to base_path
    required_dirs = [
        "data/raw",
        "data/processed"
    ]
    
    success = True
    for dir_path in required_dirs:
        full_path = base / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
        except OSError as e:
            print(f"Error creating directory {full_path}: {e}")
            success = False
    
    return success

def main():
    """
    Main entry point for creating data directories.
    
    This function is designed to be run as a script to ensure the
    required data directories exist before other pipeline tasks run.
    """
    # Determine base path: use command line arg or current directory
    base_path = sys.argv[1] if len(sys.argv) > 1 else "."
    
    print(f"Creating data directories under: {Path(base_path).absolute()}")
    
    if create_data_directories(base_path):
        print("SUCCESS: All required data directories created.")
        # List created directories for verification
        base = Path(base_path)
        for dir_path in ["data/raw", "data/processed"]:
            full_path = base / dir_path
            if full_path.exists():
                print(f"  - {full_path} exists")
        return 0
    else:
        print("FAILURE: Some directories could not be created.")
        return 1

if __name__ == "__main__":
    sys.exit(main())