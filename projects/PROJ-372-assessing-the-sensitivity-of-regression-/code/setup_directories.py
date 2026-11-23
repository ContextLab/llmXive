"""
Script to create the required directory structure for the project.
This ensures all data and artifact directories exist with .gitkeep files
to preserve them in version control.
"""
import os
from pathlib import Path

def create_directories():
    """Create the required directory structure."""
    # Define the directories to create
    directories = [
        "data/raw",
        "data/processed",
        "artifacts/profiles",
        "artifacts/stability",
        "artifacts/meta_analysis",
        "artifacts/checkpoints"
    ]

    # Create each directory and its .gitkeep file
    for dir_path in directories:
        path = Path(dir_path)
        path.mkdir(parents=True, exist_ok=True)
        
        # Create .gitkeep file to ensure directory is tracked by git
        gitkeep_path = path / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.touch()
            print(f"Created: {dir_path}/.gitkeep")
        else:
            print(f"Exists: {dir_path}/.gitkeep")
        
        print(f"Created: {dir_path}")

    print("\nDirectory structure setup complete.")

if __name__ == "__main__":
    create_directories()
