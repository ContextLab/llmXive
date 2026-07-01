import os
import sys
from pathlib import Path

def create_directories():
    """
    Create the required subdirectories for the project structure.
    Specifically creates:
    - code/data/
    - code/models/
    - code/analysis/
    
    Also ensures parent directories exist.
    """
    base_path = Path(__file__).resolve().parent.parent
    
    # Define the directories to create relative to the project root
    directories = [
        "code/data",
        "code/models",
        "code/analysis"
    ]
    
    created = []
    for dir_path in directories:
        full_path = base_path / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created.append(str(full_path))
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")
    
    return created

def main():
    """Main entry point for directory creation."""
    print("Starting directory creation for PROJ-224...")
    created_dirs = create_directories()
    if created_dirs:
        print(f"Successfully created {len(created_dirs)} directories.")
    else:
        print("No new directories were created (all already exist).")
    return 0

if __name__ == "__main__":
    sys.exit(main())
