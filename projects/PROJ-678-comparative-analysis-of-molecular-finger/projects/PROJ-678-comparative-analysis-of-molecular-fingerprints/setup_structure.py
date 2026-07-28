"""
Script to initialize the project directory structure for PROJ-678.
This script creates the necessary folders: data/raw, data/processed, code, tests.
It also creates .gitkeep files in data directories to ensure they are tracked by git.
"""
import os
from pathlib import Path

def main():
    # Define the project root
    project_root = Path("projects/PROJ-678-comparative-analysis-of-molecular-fingerprints")
    
    # Define the directories to create
    directories = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "code",
        project_root / "tests",
    ]
    
    # Create directories
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")
    
    # Create .gitkeep files in data directories
    gitkeep_paths = [
        project_root / "data" / "raw" / ".gitkeep",
        project_root / "data" / "processed" / ".gitkeep",
    ]
    
    for gitkeep_path in gitkeep_paths:
        gitkeep_path.touch()
        print(f"Created .gitkeep file: {gitkeep_path}")
    
    print("Project structure initialization complete.")

if __name__ == "__main__":
    main()