import os
import sys
from pathlib import Path

def main():
    """
    Initialize the project directory structure for PROJ-799.
    Creates necessary subdirectories under the project root.
    """
    # Define the project root relative to this file's location
    # Assuming this script is at: projects/PROJ-799-statistical-properties-of-integer-partit/code/setup_structure.py
    project_root = Path(__file__).resolve().parent.parent
    
    directories = [
        "code",
        "code/utils",
        "data/raw",
        "data/processed",
        "data/schemas",
        "tests",
        "tests/data",
        "docs",
        "state",
        "state/projects"
    ]
    
    for dir_name in directories:
        dir_path = project_root / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")
    
    print("Project structure initialization complete.")

if __name__ == "__main__":
    main()