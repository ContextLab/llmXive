import os
import sys
from pathlib import Path

def create_directory_structure():
    """
    Creates the standard project directory structure:
    code/, tests/, data/, docs/
    
    This function ensures the root project structure exists as defined
    in the project specifications.
    """
    base_dir = Path.cwd()
    
    directories = [
        base_dir / "code",
        base_dir / "tests",
        base_dir / "data",
        base_dir / "docs"
    ]
    
    created_dirs = []
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        created_dirs.append(str(directory))
        print(f"Created directory: {directory}")
    
    return created_dirs

def main():
    """
    Entry point for the setup script.
    """
    print("Initializing project directory structure...")
    dirs = create_directory_structure()
    print(f"Successfully created {len(dirs)} directories.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
