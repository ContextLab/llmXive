"""
Script to create the required data directory structure for the project.
This implements Task T001b: Create project directory structure for data.

Creates:
- data/raw: For raw input data (NIST-JANAF, SGTE, etc.)
- data/processed: For processed and cleaned data
- data/artifacts: For model artifacts, plots, and intermediate results
"""
import os
import sys
from typing import List

# Define the required directories relative to the project root
DATA_DIRS = [
    "data/raw",
    "data/processed",
    "data/artifacts"
]

def create_directories(dirs: List[str]) -> bool:
    """
    Create the specified directories if they don't exist.
    
    Args:
        dirs: List of directory paths to create (relative to project root)
        
    Returns:
        bool: True if all directories were created successfully, False otherwise
    """
    success = True
    for dir_path in dirs:
        try:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
                print(f"Created directory: {dir_path}")
            else:
                print(f"Directory already exists: {dir_path}")
        except OSError as e:
            print(f"Error creating directory {dir_path}: {e}")
            success = False
    return success

def main():
    """Main entry point for the script."""
    print("Setting up data directory structure...")
    print(f"Project root: {os.getcwd()}")
    
    if create_directories(DATA_DIRS):
        print("Data directory structure setup completed successfully.")
        # Verify the structure
        print("\nVerifying directory structure:")
        for dir_path in DATA_DIRS:
            if os.path.exists(dir_path):
                print(f"  ✓ {dir_path}")
            else:
                print(f"  ✗ {dir_path} (missing)")
        return 0
    else:
        print("Data directory structure setup failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
