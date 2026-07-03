"""
Script to initialize the project directory structure for PROJ-269.
This script creates the necessary folders under the project root as defined in T001a.
"""
import os
import sys
from pathlib import Path

def main():
    # Determine the project root based on the task description
    # The task specifies paths relative to the project root:
    # projects/PROJ-269-assessing-the-impact-of-data-augmentatio/
    
    # We assume this script is run from the root of the repository
    # or we explicitly construct the path.
    base_path = Path("projects/PROJ-269-assessing-the-impact-of-data-augmentatio")
    
    dirs_to_create = [
        base_path / "code",
        base_path / "data" / "raw",
        base_path / "data" / "derived",
        base_path / "results",
        base_path / "tests",
        base_path / "contracts",
    ]

    created_count = 0
    for dir_path in dirs_to_create:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")

    print(f"Setup complete. {created_count} new directories created.")
    
    # Ensure __init__.py files exist in Python packages
    init_files = [
        base_path / "code" / "__init__.py",
        base_path / "tests" / "__init__.py",
    ]
    
    for init_file in init_files:
        if not init_file.exists():
            init_file.touch()
            print(f"Created empty __init__.py: {init_file}")

if __name__ == "__main__":
    main()