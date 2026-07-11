"""
Script to initialize the project directory structure.
This script creates the necessary directories for the project.
"""
import os
from pathlib import Path

def create_directories():
    """Create the standard project directory structure."""
    # Define the root based on where this script is run (project root)
    root = Path.cwd()
    
    # Directories to create based on tasks.md and plan.md
    directories = [
        "code/src",
        "code/tests",
        "code/data",
        "code/data/raw",
        "code/data/processed",
        "code/output",
        "code/output/temporal_profiles",
        "code/specs",
        "code/contracts",
        "code/figures",
        # Root level aliases if needed, though code/ is the main tree
        "src",
        "tests",
        "data",
        "data/raw",
        "data/processed",
        "output",
        "output/temporal_profiles",
        "specs",
        "contracts",
        "figures",
    ]

    created = []
    for dir_path in directories:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created.append(dir_path)
        # Ensure .gitkeep exists to track empty directories in git
        gitkeep = full_path / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()

    return created

if __name__ == "__main__":
    print("Initializing project structure...")
    created_dirs = create_directories()
    if created_dirs:
        print(f"Created directories: {', '.join(created_dirs)}")
    else:
        print("All directories already exist.")
    print("Project structure initialization complete.")