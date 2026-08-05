import os
import sys
from pathlib import Path
from setup_project import ensure_directory, create_gitkeep

def setup_directories():
    """
    Setup the directory structure for the project including data/raw,
    data/processed, and results directories with .gitkeep files.
    """
    project_root = Path(__file__).resolve().parent.parent
    
    # Define directories relative to project root
    directories = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "results"
    ]
    
    for directory in directories:
        ensure_directory(directory)
        gitkeep_path = directory / ".gitkeep"
        create_gitkeep(gitkeep_path)
        print(f"Created directory: {directory}")
        print(f"Created .gitkeep: {gitkeep_path}")
    
    return True

def main():
    """
    Main entry point for setting up directories.
    """
    print("Setting up directory structure...")
    success = setup_directories()
    if success:
        print("Directory structure setup completed successfully.")
    else:
        print("Failed to setup directory structure.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
