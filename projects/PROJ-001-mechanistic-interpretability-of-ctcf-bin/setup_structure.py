"""
Script to initialize the project directory structure.
This script creates the required folders and placeholder files as per T001a.
"""
import os
import sys
from pathlib import Path

def create_structure():
    # Define the project root relative to the script location or current working directory
    # The task implies we are running this from the project root or creating it.
    # We will assume the script is run from the parent directory of 'projects'
    # or we create the 'projects' folder if it doesn't exist.
    
    base_dir = Path.cwd()
    project_root = base_dir / "projects" / "PROJ-001-mechanistic-interpretability-of-ctcf-bin"
    
    # Define the directory tree to create
    dirs = [
        project_root / "code",
        project_root / "code" / "data",
        project_root / "code" / "models",
        project_root / "code" / "interpret",
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "tests" / "unit",
        project_root / "tests" / "integration",
        project_root / "state",
    ]

    # Create directories
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {d}")

    # Create __init__.py files where needed
    init_files = [
        project_root / "code" / "__init__.py",
        project_root / "tests" / "__init__.py",
        project_root / "state" / "__init__.py",
    ]

    for f in init_files:
        if not f.exists():
            f.touch()
            print(f"Created empty file: {f}")
        else:
            print(f"File already exists: {f}")

    print(f"\nProject structure initialized at: {project_root}")

if __name__ == "__main__":
    create_structure()