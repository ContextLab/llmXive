import os
import sys
from pathlib import Path

def create_directories():
    """
    Creates the required project directory structure for PROJ-511.
    Ensures all directories exist and are ready for data/code storage.
    """
    base_path = Path(__file__).resolve().parent.parent
    
    directories = [
        "code",
        "data",
        "data/raw_cif",
        "models",
        "results",
        "contracts",
        "specs"
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
    
    print(f"Directory setup complete. {created_count} new directories created.")
    return True

if __name__ == "__main__":
    success = create_directories()
    sys.exit(0 if success else 1)
