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
    # Define the project root (assuming this script is in code/, root is parent)
    project_root = Path(__file__).resolve().parent.parent
    
    # Define the directories to create
    directories = [
        "data/raw",
        "data/processed",
        "data/results",
        "data/logs",
        "contracts"
    ]
    
    created_paths = []
    errors = []
    
    for dir_name in directories:
        target_path = project_root / dir_name
        try:
            target_path.mkdir(parents=True, exist_ok=True)
            created_paths.append(str(target_path))
            print(f"Created directory: {target_path}")
        except OSError as e:
            error_msg = f"Failed to create directory {target_path}: {e}"
            errors.append(error_msg)
            print(error_msg, file=sys.stderr)
    
    if errors:
        return False
    
    return True

if __name__ == "__main__":
    success = create_directories()
    sys.exit(0 if success else 1)