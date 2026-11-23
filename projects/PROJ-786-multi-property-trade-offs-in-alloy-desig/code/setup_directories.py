"""
Script to initialize the project directory structure for PROJ-786.
This script creates the required folder hierarchy and .gitkeep files
to ensure the directories are tracked in version control.
"""
import os
from pathlib import Path

def create_directory_structure():
    """
    Creates the full directory structure for the project.
    """
    # Define the root project directory
    root = Path("projects/PROJ-786-multi-property-trade-offs-in-alloy-desig")
    
    # Define all required directories relative to the root
    directories = [
        "code",
        "data",
        "data/raw",
        "data/processed",
        "tests",
        "tests/contract",
        "tests/integration",
        "tests/unit",
        "docs"
    ]

    created_count = 0
    for dir_name in directories:
        dir_path = root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {dir_path}")
        else:
            print(f"Directory already exists: {dir_path}")

    # Create .gitkeep files in each directory
    for dir_name in directories:
        dir_path = root / dir_name
        gitkeep_path = dir_path / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.touch()
            print(f"Created .gitkeep: {gitkeep_path}")
        else:
            print(f".gitkeep already exists: {gitkeep_path}")

    print(f"\nProject structure initialization complete. Created {created_count} new directories.")
    return root

if __name__ == "__main__":
    create_directory_structure()