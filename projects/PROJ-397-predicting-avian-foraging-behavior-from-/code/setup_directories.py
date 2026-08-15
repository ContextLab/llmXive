"""
Script to initialize all required project directories.
This script ensures that the project structure is correctly set up
before running any data processing or modeling tasks.
"""
import os
import sys
from pathlib import Path

def main():
    """Create all necessary project directories."""
    # Define the project root based on the task description
    # The task specifies: projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/
    # However, since we are running from within the code directory or as a module,
    # we assume the script is run from the root where 'code' is a subdirectory.
    # To be safe, we construct paths relative to the script's location or CWD.
    
    # Assuming the script is in code/ or code/setup_directories.py
    # We need to create directories under code/
    
    base_dir = Path(__file__).parent
    
    directories = [
        "data",
        "models",
        "viz",
        "notebooks",
        "utils",
        "tests"
    ]
    
    created_dirs = []
    
    for dir_name in directories:
        dir_path = base_dir / dir_name
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(dir_path))
            
            # Create .gitkeep in each directory
            gitkeep_path = dir_path / ".gitkeep"
            if not gitkeep_path.exists():
                gitkeep_path.touch()
            created_dirs.append(f"  (created {gitkeep_path.name})")
            
            print(f"Created directory: {dir_path}")
        except Exception as e:
            print(f"Error creating directory {dir_path}: {e}")
            sys.exit(1)
    
    print(f"\nSuccessfully created {len(directories)} directories with .gitkeep files.")
    return 0

if __name__ == "__main__":
    sys.exit(main())