import os
import sys
from pathlib import Path

def create_directories():
    """
    Create the required project directory structure for data and contracts.
    
    Creates the following directories relative to the project root:
    - data/raw/
    - data/processed/
    - data/results/
    - data/logs/
    - contracts/
    
    Returns:
        bool: True if all directories were created successfully, False otherwise.
    """
    # Determine project root (assuming script is run from project root or code/ subdirectory)
    # We use the parent of this file's directory to ensure we are at the project root
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent
    
    directories_to_create = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "results",
        project_root / "data" / "logs",
        project_root / "contracts",
    ]
    
    success = True
    for directory in directories_to_create:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory}")
        except OSError as e:
            print(f"Error creating directory {directory}: {e}")
            success = False
    
    return success

if __name__ == "__main__":
    if create_directories():
        print("All required directories created successfully.")
        sys.exit(0)
    else:
        print("Failed to create one or more directories.")
        sys.exit(1)