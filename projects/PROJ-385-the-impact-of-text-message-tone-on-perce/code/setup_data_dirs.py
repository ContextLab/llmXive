"""
Script to create the data directory structure for the project.
Creates data/raw, data/processed, and data/consent directories.
Adds .gitkeep files to ensure they are tracked by git.
"""
import os
from pathlib import Path
from config import get_project_root, get_raw_data_dir, get_processed_data_dir, get_consent_dir


def create_directories():
    """Create the required data directory structure."""
    project_root = get_project_root()
    
    # Define the directories to create
    directories = [
        get_raw_data_dir(),
        get_processed_data_dir(),
        get_consent_dir(),
    ]
    
    # Create directories and .gitkeep files
    for dir_path in directories:
        dir_path.mkdir(parents=True, exist_ok=True)
        gitkeep_path = dir_path / ".gitkeep"
        gitkeep_path.touch()
        print(f"Created: {dir_path}")
        print(f"  -> Added .gitkeep: {gitkeep_path}")
    
    print(f"\nData directory structure created successfully in {project_root}")


def main():
    """Main entry point."""
    create_directories()


if __name__ == "__main__":
    main()
