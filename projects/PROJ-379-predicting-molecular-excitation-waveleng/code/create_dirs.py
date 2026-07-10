"""
Script to initialize the project directory structure for PROJ-379.

Creates the required directories for data storage, code implementation,
testing, and documentation as specified in task T001a.
"""
import os
from pathlib import Path

def main():
    # Define the project root based on the task description
    # The task specifies creating these in projects/PROJ-379-predicting-molecular-excitation-waveleng/
    # We assume the script is run from the repository root or the project root.
    # To be safe, we define the base relative to the script location if needed,
    # but typically in these pipelines, the working directory is the project root.
    
    project_root = Path.cwd()
    
    # Check if we are already inside the specific project folder or need to navigate there.
    # The task says: "in projects/PROJ-379-predicting-molecular-excitation-waveleng/"
    # If the current dir is the repo root, we need to enter that folder.
    # If the current dir is already the project folder, we just create the subdirs.
    
    target_dir_name = "PROJ-379-predicting-molecular-excitation-waveleng"
    
    # Determine the actual base path to create directories under
    if project_root.name == target_dir_name:
        base_path = project_root
    elif (project_root / target_dir_name).exists():
        base_path = project_root / target_dir_name
    else:
        # If neither, assume we are running from the repo root and create the project folder first
        base_path = project_root / target_dir_name
    
    print(f"Creating directory structure under: {base_path}")
    
    # Define the directories to create relative to the base path
    dirs_to_create = [
        "data/raw",
        "data/processed",
        "code",
        "tests",
        "docs"
    ]
    
    created_count = 0
    for dir_path in dirs_to_create:
        full_path = base_path / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created: {full_path}")
            created_count += 1
        else:
            print(f"Exists: {full_path}")
    
    print(f"Directory structure initialization complete. {created_count} new directories created.")

if __name__ == "__main__":
    main()