"""
Project Initialization Script for PROJ-064.
Creates the standard directory structure required for the statistical discrepancies pipeline.
"""
import os
import sys
from pathlib import Path

def initialize_project_structure(root_dir: str) -> None:
    """
    Creates the directory structure for the project.
    
    Structure:
    projects/PROJ-064-statistical-discrepancies-in-publicly-av/
    ├── code/
    ├── data/
    │   ├── raw/
    │   └── processed/
    ├── tests/
    ├── docs/
    ├── state/
    └── config/
    
    Args:
        root_dir: The base directory where the project folder will be created.
    """
    project_name = "PROJ-064-statistical-discrepancies-in-publicly-av"
    project_root = Path(root_dir) / project_name
    
    # Define all required directories
    directories = [
        project_root / "code",
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "tests",
        project_root / "docs",
        project_root / "state",
        project_root / "config",
    ]
    
    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory.relative_to(project_root)}")
            created_count += 1
        else:
            print(f"Directory already exists: {directory.relative_to(project_root)}")
    
    if created_count > 0:
        print(f"\nSuccessfully initialized project structure at: {project_root}")
    else:
        print("\nProject structure already fully initialized.")

if __name__ == "__main__":
    # Default to current working directory if no argument provided
    base_path = sys.argv[1] if len(sys.argv) > 1 else "."
    initialize_project_structure(base_path)
