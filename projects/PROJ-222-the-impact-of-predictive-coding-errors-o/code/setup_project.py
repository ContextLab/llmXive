import os
import sys
from pathlib import Path

def create_directories():
    """
    Creates the project directory structure as defined in the implementation plan.
    
    Required directories:
    - data/raw
    - data/processed
    - code (already exists as parent, but ensures path)
    - figures
    - analysis
    - contracts
    
    Returns:
        bool: True if all directories were created or already exist.
    """
    # Define the project root (assuming this script is in code/ or project root)
    # We use the current working directory as the project root for this task
    project_root = Path.cwd()
    
    directories = [
        "data/raw",
        "data/processed",
        "code",
        "figures",
        "analysis",
        "contracts"
    ]
    
    created_count = 0
    for dir_name in directories:
        dir_path = project_root / dir_name
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            if dir_path.is_dir():
                print(f"Created or verified directory: {dir_path}")
                created_count += 1
            else:
                print(f"ERROR: Failed to create directory: {dir_path}")
                return False
        except PermissionError:
            print(f"ERROR: Permission denied creating directory: {dir_path}")
            return False
        except Exception as e:
            print(f"ERROR: Failed to create directory {dir_path}: {e}")
            return False
    
    print(f"Successfully created/verified {created_count}/{len(directories)} directories.")
    return True

if __name__ == "__main__":
    success = create_directories()
    sys.exit(0 if success else 1)