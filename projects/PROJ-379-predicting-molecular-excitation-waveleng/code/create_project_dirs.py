"""
Task T001a: Create project directory structure.

Creates the following directories under projects/PROJ-379-predicting-molecular-excitation-waveleng/:
- data/raw
- data/processed
- code
- tests
- docs
"""
import os
from pathlib import Path
import sys

def main():
    # Define the project root based on the task description
    # The task specifies creating these in the project directory
    project_name = "PROJ-379-predicting-molecular-excitation-waveleng"
    base_dir = Path("projects") / project_name
    
    # Directories to create
    required_dirs = [
        "data/raw",
        "data/processed",
        "code",
        "tests",
        "docs"
    ]
    
    created_count = 0
    for dir_path in required_dirs:
        full_path = base_dir / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        except OSError as e:
            print(f"Error creating directory {full_path}: {e}", file=sys.stderr)
            return 1
    
    print(f"Successfully created {created_count} directories for {project_name}.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
