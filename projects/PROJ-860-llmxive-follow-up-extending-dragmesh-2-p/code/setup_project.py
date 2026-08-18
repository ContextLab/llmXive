import os
import sys
from pathlib import Path

def main():
    """
    Execute the creation of the project directory structure.
    This script implements T001a: Create project directory structure.
    """
    # Define the project root relative to the script location or current working directory
    # The task specifies the structure relative to the project root.
    # We assume the script is run from the project root or we create it relative to cwd.
    project_root = Path.cwd()
    
    # Define the required directories based on T001a description
    # "Execute `mkdir -p code tests data/raw data/generated state/projects data/results`"
    directories = [
        "code",
        "tests",
        "data/raw",
        "data/generated",
        "state/projects",
        "data/results"
    ]
    
    created_paths = []
    for dir_name in directories:
        full_path = project_root / dir_name
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            created_paths.append(str(full_path.relative_to(project_root)))
            print(f"Created directory: {full_path}")
        except OSError as e:
            print(f"Error creating directory {full_path}: {e}")
            sys.exit(1)
    
    print(f"Successfully created {len(created_paths)} directories.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
