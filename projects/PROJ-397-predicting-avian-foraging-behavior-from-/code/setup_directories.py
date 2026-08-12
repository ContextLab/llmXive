import os
import sys
from pathlib import Path

def main():
    """
    Initialize the project directory structure for PROJ-397.
    Creates the required subdirectories and placeholder files.
    """
    # Define the project root based on the task description
    # The task specifies: projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/
    # We assume the script is run from the repository root, so we construct the path relative to CWD
    project_root = Path.cwd() / "projects" / "PROJ-397-predicting-avian-foraging-behavior-from-" / "code"
    
    # Create the base code directory if it doesn't exist
    project_root.mkdir(parents=True, exist_ok=True)
    
    # Define subdirectories to create
    subdirs = [
        "data",
        "models",
        "viz",
        "notebooks",
        "utils",
        "tests"
    ]
    
    # Create subdirectories
    for subdir in subdirs:
        dir_path = project_root / subdir
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")
    
    # Create placeholder files
    placeholder_files = [
        "requirements.txt",
        "run_pipeline.sh",
        "README.md"
    ]
    
    for filename in placeholder_files:
        file_path = project_root / filename
        if not file_path.exists():
            file_path.touch()
            print(f"Created placeholder file: {file_path}")
        else:
            print(f"File already exists: {file_path}")
    
    print(f"Project structure initialized at: {project_root}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
