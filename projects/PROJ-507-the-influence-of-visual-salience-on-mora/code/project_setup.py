"""
Project Setup Module
Handles the creation of the project directory structure as per the implementation plan.
"""
import os
from pathlib import Path


def create_project_structure():
    """
    Creates the required project directory structure.
    
    Creates the following directories relative to the project root:
    - code/
    - data/raw/
    - data/processed/
    - data/survey/
    - data/synth/ (added for data separation compliance)
    - tests/
    - specs/
    - docs/
    - config/
    - figures/
    
    Returns:
        list: A list of created directory paths as strings.
    """
    # Define the root directory (current working directory)
    root = Path.cwd()
    
    # Define the directory structure to create
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/survey",
        "data/synth",  # Added for strict data separation (real vs synthetic)
        "tests",
        "specs",
        "docs",
        "config",
        "figures"
    ]
    
    created_dirs = []
    
    for dir_path in directories:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(full_path))
            print(f"Created directory: {full_path}")
        else:
            # Ensure it is actually a directory
            if full_path.is_dir():
                created_dirs.append(str(full_path))
                print(f"Directory already exists: {full_path}")
            else:
                raise FileExistsError(f"Path exists but is not a directory: {full_path}")
    
    # Create .gitkeep files to ensure directories are tracked by git
    for dir_path in directories:
        full_path = root / dir_path
        gitkeep_path = full_path / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.touch()
            print(f"Created .gitkeep in: {full_path}")
    
    return created_dirs


if __name__ == "__main__":
    print("Initializing project structure...")
    created = create_project_structure()
    print(f"\nSuccessfully created/verified {len(created)} directories.")
    print("Project structure is ready.")
