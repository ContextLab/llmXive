"""
Setup script to create the required project directory structure.
Implements Task T001: Create project directories explicitly.
"""
import os
import sys
from pathlib import Path

def create_directories():
    """
    Creates the required directory structure for the project.
    
    Directories created:
    - code/
    - data/raw
    - data/processed
    - data/results
    - specs/001-investigating-the-correlation-between-gu/contracts/
    
    Returns:
        bool: True if all directories were created successfully, False otherwise.
    """
    # Define the project root (assumed to be the parent of the code/ directory)
    # We use the current working directory as the root for this script
    root = Path.cwd()
    
    # Define relative paths based on the task requirements
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/results",
        "specs/001-investigating-the-correlation-between-gu/contracts",
    ]
    
    created_count = 0
    existing_count = 0
    
    for dir_path in directories:
        full_path = root / dir_path
        try:
            # exist_ok=True ensures we don't error if the directory already exists
            full_path.mkdir(parents=True, exist_ok=True)
            if full_path.is_dir():
                created_count += 1
                print(f"Created/Verified directory: {full_path}")
            else:
                print(f"ERROR: Path exists but is not a directory: {full_path}")
                return False
        except Exception as e:
            print(f"ERROR: Failed to create directory {full_path}: {e}")
            return False
    
    print(f"\nDirectory setup complete.")
    print(f"  New/Verified: {created_count}")
    print(f"  Total required: {len(directories)}")
    return True

if __name__ == "__main__":
    success = create_directories()
    sys.exit(0 if success else 1)
