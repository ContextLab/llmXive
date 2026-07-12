import os
import sys
from pathlib import Path

def create_directories():
    """
    Creates the required project directory structure for PROJ-425.
    Directories created:
      - code/
      - data/raw/
      - data/processed/
      - tests/unit
      - tests/integration
    """
    # Define the project root (assuming this script is in code/ or project root)
    # We use the current working directory as the project root for flexibility
    project_root = Path.cwd()
    
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "tests/unit",
        "tests/integration"
    ]
    
    created_dirs = []
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(full_path))
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")
    
    return created_dirs

def main():
    """Entry point for directory creation."""
    print("Initializing project structure for molecular complexity analysis...")
    created = create_directories()
    if created:
        print(f"Successfully created {len(created)} new directories.")
    else:
        print("All directories already existed.")
    print("Project structure ready.")

if __name__ == "__main__":
    main()