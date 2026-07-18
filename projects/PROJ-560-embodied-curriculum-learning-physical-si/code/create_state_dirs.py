"""
Script to create the required state directories for the project.

This script creates the directory structure under:
projects/PROJ-560-embodied-curriculum-learning-physical-si/state/projects/PROJ-560-embodied-curriculum-learning-physical-si/

It ensures the path exists and creates any missing parent directories.
"""
import os
import sys
from pathlib import Path

def create_directory(path: Path) -> None:
    """Create a directory if it does not exist."""
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {path}")
    else:
        print(f"Directory already exists: {path}")

def main() -> int:
    """Main entry point for creating state directories."""
    # Define the base project root relative to where this script is run
    # Assuming the script is run from the project root or code/ directory
    # We need to construct the path relative to the project root.
    # The task specifies: projects/PROJ-560-embodied-curriculum-learning-physical-si/state/projects/PROJ-560-embodied-curriculum-learning-physical-si/
    
    # Determine the project root. If running from code/, go up one level.
    # If running from root, use current dir.
    current_dir = Path.cwd()
    project_root = current_dir
    
    # Check if we are inside the project directory
    # The path structure suggests the project is named PROJ-560-embodied-curriculum-learning-physical-si
    # and resides under a `projects` folder.
    
    # Let's assume the script is run from the root of the repository.
    # The target path is relative to the repository root.
    target_path_str = "projects/PROJ-560-embodied-curriculum-learning-physical-si/state/projects/PROJ-560-embodied-curriculum-learning-physical-si"
    target_path = project_root / target_path_str
    
    print(f"Creating state directory at: {target_path}")
    create_directory(target_path)
    
    # Also create a subdirectory for project state if needed, 
    # though the task path seems to be the leaf itself.
    # To be safe, let's ensure the leaf is a directory.
    
    return 0

if __name__ == "__main__":
    sys.exit(main())