"""
Script to initialize the project directory structure.
This script is executed once to ensure all required folders exist.
"""
import os
import sys
from pathlib import Path
from typing import List

def create_directory_structure() -> List[str]:
    """
    Creates the standard project directory structure.
    Returns a list of created directory paths.
    """
    root = Path(__file__).parent
    
    # Define all required directories relative to the project root
    directories = [
        "code",
        "code/data",
        "code/utils",
        "tests",
        "data",
        "data/raw",
        "data/processed",
        "state",
        "state/projects",
        "specs",
        "specs/001-molecular-flexibility-permeability",
        "specs/001-molecular-flexibility-permeability/contracts",
        "figures",
        "logs",
        "scripts"
    ]
    
    created = []
    for dir_path in directories:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created.append(str(full_path))
            print(f"Created directory: {full_path}")
        else:
            # Ensure it's actually a directory
            if not full_path.is_dir():
                raise RuntimeError(f"Path exists but is not a directory: {full_path}")
    
    # Create __init__.py files in all Python packages
    package_dirs = ["code", "code/data", "code/utils", "tests", "data", "state", "state/projects", "specs", "specs/001-molecular-flexibility-permeability", "specs/001-molecular-flexibility-permeability/contracts", "figures", "logs", "scripts"]
    for pkg_dir in package_dirs:
        pkg_path = root / pkg_dir / "__init__.py"
        if not pkg_path.exists():
            pkg_path.touch()
            print(f"Created package init: {pkg_path}")
        
    return created

def main():
    """Entry point for the setup script."""
    print("Initializing project structure...")
    try:
        created_dirs = create_directory_structure()
        print(f"Successfully created {len(created_dirs)} directories.")
        print("Project structure is ready.")
        return 0
    except Exception as e:
        print(f"Error setting up project structure: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())