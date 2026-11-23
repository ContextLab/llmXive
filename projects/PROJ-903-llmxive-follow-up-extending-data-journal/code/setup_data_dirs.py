"""
Script to initialize the required data directory structure for the project.
Creates 'data/raw', 'data/processed', and 'output' directories.
"""
import os
from pathlib import Path

def main():
    # Define the project root relative to this script's location or current working directory
    # The task specifies paths relative to the project root.
    # We will resolve them relative to the current working directory to ensure they are created where expected.
    project_root = Path.cwd()
    
    # Define the directories to create based on the task description
    # Note: The task description mentions a specific project path prefix, but standard 
    # project conventions and the existing file structure (code/, data/) imply 
    # these directories should be at the project root level.
    # We create 'data/raw', 'data/processed', and 'output' relative to the current directory.
    
    directories = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "output"
    ]
    
    created_count = 0
    for dir_path in directories:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")
    
    print(f"Setup complete. {created_count} new directories created.")

if __name__ == "__main__":
    main()