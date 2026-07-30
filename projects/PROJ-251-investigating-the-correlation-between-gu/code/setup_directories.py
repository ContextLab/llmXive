import os
import sys
from pathlib import Path

def create_directories():
    """
    Create the required project directory structure:
    - code/
    - data/raw
    - data/processed
    - data/results
    - specs/001-investigating-the-correlation-between-gu/contracts/
    
    Returns:
        bool: True if all directories were created or already exist, False otherwise.
    """
    base_path = Path(__file__).resolve().parent.parent
    
    directories = [
        base_path / "code",
        base_path / "data" / "raw",
        base_path / "data" / "processed",
        base_path / "data" / "results",
        base_path / "specs" / "001-investigating-the-correlation-between-gu" / "contracts"
    ]
    
    success = True
    for directory in directories:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created/Verified directory: {directory}")
        except OSError as e:
            print(f"Error creating directory {directory}: {e}")
            success = False
    
    return success

if __name__ == "__main__":
    success = create_directories()
    if success:
        print("All directories created successfully.")
        sys.exit(0)
    else:
        print("Failed to create some directories.")
        sys.exit(1)
