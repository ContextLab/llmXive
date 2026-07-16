"""
Data directory structure setup utility.
Creates the required data folders (.gitkeep) for the project.
"""
import os
import sys
from pathlib import Path

# Ensure we can import from the project root if run as a script
# However, since this task is specifically about creating the structure,
# we will use the standard library pathlib to do the work directly.

def setup_data_directories():
    """
    Creates the data/raw, data/processed, and data/results directories
    with .gitkeep files to ensure they are tracked by git.
    
    This script assumes it is run from the project root or that the 
    'projects/PROJ-496-the-influence-of-simulated-social-valida' 
    structure exists relative to the current working directory.
    """
    # Determine the project root based on the task description
    # The task asks for paths under the project root.
    # We will assume the script is run from the project root.
    # If the project is in a subdirectory, we adjust.
    
    # Based on T001a-evidence, the project root is:
    # projects/PROJ-496-the-influence-of-simulated-social-valida/
    # But the task description says "relative to the project root".
    # We will create the directories relative to the current working directory.
    # The user will run this from the project root.
    
    project_root = Path.cwd()
    
    # Define the data directories
    data_dirs = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "results"
    ]
    
    created_dirs = []
    
    for dir_path in data_dirs:
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            gitkeep_path = dir_path / ".gitkeep"
            gitkeep_path.touch(exist_ok=True)
            created_dirs.append(str(dir_path))
            print(f"Created: {dir_path}")
            print(f"  -> Added .gitkeep: {gitkeep_path}")
        except Exception as e:
            print(f"Error creating directory {dir_path}: {e}")
            return 1
            
    print(f"\nSuccessfully created {len(created_dirs)} data directories.")
    return 0

if __name__ == "__main__":
    sys.exit(setup_data_directories())