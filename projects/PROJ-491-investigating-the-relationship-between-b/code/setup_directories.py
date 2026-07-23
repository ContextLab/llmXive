import os
import sys
from pathlib import Path
from config import ensure_directories

def create_directories():
    """
    Creates the required project directory structure:
    code/, tests/, data/raw/, data/processed/, state/
    
    This function ensures all directories exist as per T001a.
    """
    # Define the root directory (assumed to be the project root)
    # We assume this script is run from the project root or passed the root path.
    # For safety, we use the current working directory as the base.
    base_path = Path.cwd()
    
    directories = [
        "code",
        "tests",
        "data/raw",
        "data/processed",
        "state"
    ]
    
    created_count = 0
    for dir_name in directories:
        dir_path = base_path / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")
    
    if created_count > 0:
        print(f"Successfully created {created_count} new directory(s).")
    else:
        print("All required directories already exist.")
        
    # Ensure the parent directories for data exist too
    ensure_directories()

def main():
    create_directories()

if __name__ == "__main__":
    main()
