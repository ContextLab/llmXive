"""
Setup script to create the project directory structure.
"""
import os
import sys
from pathlib import Path

def main():
    # Define the project root based on the current working directory context
    # The script is expected to be run from the project root or the code directory.
    # We will assume the script is run from the project root 'projects/PROJ-470-...'
    # or we need to resolve it relative to the script location if run as a module.
    # Given the task description, we target the specific project path.
    
    # Determine the base directory. If run from the project root, use that.
    # If run from code/, go up one level.
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    
    # Verify we are in the expected project
    expected_project_name = "PROJ-470-predicting-cognitive-fatigue-from-restin"
    if project_root.name != expected_project_name:
        # If not, try to find the parent that matches, or assume current dir is root
        # For robustness, we assume the command is run from the project root
        # but if the file is in code/, we go up.
        pass 
    
    # Define the directories to create
    # Based on T001: projects/PROJ-470.../data/raw, etc.
    # Since script is in code/, project_root is the project root.
    
    dirs_to_create = [
        "data/raw",
        "data/processed",
        "data/analysis",
        "code",
        "tests/unit",
        "tests/integration",
        "docs"
    ]
    
    created_count = 0
    for dir_path in dirs_to_create:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"Setup complete. Created {created_count} new directories.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
