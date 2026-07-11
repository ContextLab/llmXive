import os
import sys
from pathlib import Path
from setup_project import ensure_directory, create_gitkeep

def setup_directories():
    """
    Setup the required directory structure for the project.
    Creates data/raw, data/processed, and results directories with .gitkeep files.
    """
    # Define the relative paths to create
    directories = [
        "data/raw",
        "data/processed",
        "results"
    ]

    # Get the project root (assumed to be the parent of the 'code' directory)
    # Since this script is in 'code/', we go up one level
    project_root = Path(__file__).resolve().parent.parent

    created_paths = []
    for dir_name in directories:
        full_path = project_root / dir_name
        ensure_directory(full_path)
        gitkeep_path = full_path / ".gitkeep"
        create_gitkeep(gitkeep_path)
        created_paths.append(str(full_path))
        print(f"Created directory: {full_path}")
        print(f"Created .gitkeep: {gitkeep_path}")

    return created_paths

def main():
    """Entry point for the directory setup script."""
    print("Starting directory setup for PROJ-355...")
    setup_directories()
    print("Directory setup complete.")

if __name__ == "__main__":
    main()
