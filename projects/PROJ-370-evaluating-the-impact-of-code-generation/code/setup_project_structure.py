import os
import sys
from pathlib import Path

def create_directories():
    """
    Creates the required project directory structure for the llmXive research pipeline.
    Directories created:
      - src/
      - data/raw/
      - data/derived/
      - data/annotations/
      - results/
      - tests/
      - specs/
    """
    # Define the base path relative to the script location (project root)
    # Assuming the script is run from the project root or the path is passed correctly.
    # Based on the API surface, we assume the script is at code/setup_project_structure.py
    # and needs to create dirs relative to the repo root (parent of code/).
    
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent
    
    directories = [
        project_root / "src",
        project_root / "data" / "raw",
        project_root / "data" / "derived",
        project_root / "data" / "annotations",
        project_root / "results",
        project_root / "tests",
        project_root / "specs"
    ]
    
    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory}")
            created_count += 1
        else:
            print(f"Directory already exists: {directory}")
    
    print(f"Project structure setup complete. {created_count} new directories created.")
    return created_count

def main():
    """Entry point for the script."""
    create_directories()

if __name__ == "__main__":
    main()