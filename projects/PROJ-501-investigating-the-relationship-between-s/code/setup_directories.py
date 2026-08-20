import os
import sys
from pathlib import Path

def create_directories():
    """
    Creates the required project directory structure for data and contracts.
    
    Directories created:
    - data/raw/
    - data/processed/
    - data/results/
    - data/logs/
    - contracts/
    
    Returns:
        bool: True if all directories were created successfully, False otherwise.
    """
    base_path = Path(__file__).resolve().parent.parent
    
    directories = [
        "data/raw",
        "data/processed",
        "data/results",
        "data/logs",
        "contracts"
    ]
    
    created_count = 0
    for dir_name in directories:
        full_path = base_path / dir_name
        try:
            if not full_path.exists():
                full_path.mkdir(parents=True, exist_ok=True)
                print(f"Created directory: {full_path}")
                created_count += 1
            else:
                print(f"Directory already exists: {full_path}")
        except OSError as e:
            print(f"Error creating directory {full_path}: {e}")
            return False
    
    print(f"Successfully created {created_count} new directories.")
    return True

if __name__ == "__main__":
    success = create_directories()
    sys.exit(0 if success else 1)
