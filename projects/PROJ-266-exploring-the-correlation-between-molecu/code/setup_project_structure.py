import os
import sys
from pathlib import Path
from typing import List

def create_directory_structure() -> List[Path]:
    """
    Create the project directory structure as per the implementation plan.
    
    Creates the following directories relative to the project root:
    - code/
    - code/utils/
    - code/data/
    - tests/
    - tests/contract/
    - data/
    - data/raw/
    - data/processed/
    - data/interim/
    - figures/
    - state/
    - state/projects/
    - specs/
    
    Returns:
        List[Path]: List of created directory paths.
    """
    # Define the base directories relative to the project root
    base_dirs = [
        "code",
        "code/utils",
        "code/data",
        "tests",
        "tests/contract",
        "data",
        "data/raw",
        "data/processed",
        "data/interim",
        "figures",
        "state",
        "state/projects",
        "specs",
    ]
    
    project_root = Path.cwd()
    created_dirs: List[Path] = []
    
    for dir_path in base_dirs:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(full_path)
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")
            
    return created_dirs

def main():
    """Main entry point for the project structure setup."""
    print("Setting up project directory structure...")
    created = create_directory_structure()
    print(f"\nSuccessfully created {len(created)} directories.")
    print("Project structure is ready for implementation.")

if __name__ == "__main__":
    main()
