"""
Setup script to create the project directory structure for PROJ-874-llmxive-follow-up-extending-enhancing-tr.
This script creates the required directories under the 'projects/' folder.
"""
import os
import sys
from pathlib import Path

def create_directory_structure():
    """
    Creates the project directory structure:
    projects/PROJ-874-llmxive-follow-up-extending-enhancing-tr/
        ├── code/
        ├── data/
        ├── tests/
        └── docs/
    """
    # Define the project root directory
    project_root = Path("projects/PROJ-874-llmxive-follow-up-extending-enhancing-tr")
    
    # Define subdirectories
    subdirs = [
        "code",
        "data",
        "tests",
        "docs"
    ]
    
    # Create the project root directory
    project_root.mkdir(parents=True, exist_ok=True)
    print(f"Created project root: {project_root}")
    
    # Create subdirectories
    for subdir in subdirs:
        dir_path = project_root / subdir
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")
    
    # Create a .gitkeep file in each directory to ensure they are tracked by git
    for subdir in subdirs:
        dir_path = project_root / subdir
        gitkeep_path = dir_path / ".gitkeep"
        gitkeep_path.touch()
        print(f"Created .gitkeep in: {gitkeep_path}")
    
    print("\nDirectory structure creation completed successfully.")
    return True

def main():
    """Main entry point for the script."""
    try:
        create_directory_structure()
        return 0
    except Exception as e:
        print(f"Error creating directory structure: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())