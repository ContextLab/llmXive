"""
Script to set up the required data directory structure for the project.
Creates:
  - data/raw/
  - data/processed/
  - state/projects/
"""
import os
import sys
from pathlib import Path

def main():
    """Create the required directory structure."""
    # Determine project root (assuming script is in code/ or code/code/)
    # We need to find the root relative to the project structure.
    # Based on tasks.md, paths are relative to project root.
    # The script is at code/setup_data_structure.py.
    
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    # If we are in code/code/, go up one level. If in code/, go up.
    # Let's assume standard structure: project_root/code/setup_data_structure.py
    # Or project_root/code/code/setup_data_structure.py (as per some existing files)
    
    # Check if we are in a nested code directory
    if code_dir.name == "code" and code_dir.parent.name == "code":
        project_root = code_dir.parent.parent
    elif code_dir.name == "code":
        project_root = code_dir.parent
    else:
        # Fallback: assume current working directory is project root
        project_root = Path.cwd()

    # Define the directories to create
    directories = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "state" / "projects"
    ]

    created = []
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory}")
            created.append(directory)
        else:
            print(f"Directory already exists: {directory}")

    if not created:
        print("All required directories already exist.")
    else:
        print(f"Successfully created {len(created)} directories.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
