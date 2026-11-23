"""
Script to initialize the project directory structure and placeholder files.
This script is executed to ensure the required directories exist.
"""
import os
import sys
from typing import List, Optional

def create_directory_structure(base_path: str = ".") -> None:
    """Create the core project directories."""
    directories = [
        "code",
        "data",
        "tests",
        "data/raw",
        "data/generated",
        "data/results",
    ]
    
    for dir_path in directories:
        full_path = os.path.join(base_path, dir_path)
        if not os.path.exists(full_path):
          os.makedirs(full_path)
          print(f"Created directory: {full_path}")
        else:
          print(f"Directory already exists: {full_path}")

def create_gitkeep_files(base_path: str = ".") -> None:
    """Create .gitkeep files in data subdirectories to preserve them in git."""
    data_dirs = [
        "data/raw",
        "data/generated",
        "data/results",
    ]
    
    for dir_path in data_dirs:
        full_path = os.path.join(base_path, dir_path)
        gitkeep_path = os.path.join(full_path, ".gitkeep")
        
        if not os.path.exists(gitkeep_path):
            # Create an empty file or a comment file
            with open(gitkeep_path, "w") as f:
                f.write(f"# Placeholder to ensure directory exists in git\n")
                f.write(f"# Directory: {dir_path}\n")
            print(f"Created .gitkeep: {gitkeep_path}")
        else:
            print(f".gitkeep already exists: {gitkeep_path}")

def main() -> int:
    """Entry point for the script."""
    print("Initializing project directory structure...")
    create_directory_structure(".")
    create_gitkeep_files(".")
    print("Project structure initialization complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
