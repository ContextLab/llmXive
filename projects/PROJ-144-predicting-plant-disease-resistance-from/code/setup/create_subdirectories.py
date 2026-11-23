"""
Module to create required subdirectories for the plant disease resistance project.
Implements task T001b.
"""
import os
import sys
from pathlib import Path

# Import constants from the existing utility module
from utils.constants import (
    PROJECT_ROOT,
    DATA_RAW_DIR,
    DATA_PROCESSED_DIR,
    DATA_INTERMEDIATE_DIR,
    RESULTS_PLOTS_DIR
)

def create_subdirectories():
    """
    Create the required subdirectories for data and results.
    
    Creates:
    - data/raw
    - data/processed
    - data/intermediate
    - results/plots
    
    Returns:
        bool: True if all directories were created successfully, False otherwise.
    """
    directories_to_create = [
        DATA_RAW_DIR,
        DATA_PROCESSED_DIR,
        DATA_INTERMEDIATE_DIR,
        RESULTS_PLOTS_DIR
    ]
    
    success = True
    for dir_path in directories_to_create:
        try:
            # Ensure the directory exists (creates parent dirs if needed)
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            # Verify it's a directory and writable
            if not Path(dir_path).is_dir():
                print(f"ERROR: {dir_path} was created but is not a directory.")
                success = False
            elif not os.access(dir_path, os.W_OK):
                print(f"ERROR: {dir_path} is not writable.")
                success = False
            else:
                print(f"SUCCESS: Created/verified directory: {dir_path}")
        except Exception as e:
            print(f"ERROR: Failed to create {dir_path}: {e}")
            success = False
    
    return success

def main():
    """Main entry point for script execution."""
    print(f"Creating subdirectories for project at: {PROJECT_ROOT}")
    success = create_subdirectories()
    if success:
        print("All subdirectories created successfully.")
        sys.exit(0)
    else:
        print("Failed to create one or more subdirectories.")
        sys.exit(1)

if __name__ == "__main__":
    main()