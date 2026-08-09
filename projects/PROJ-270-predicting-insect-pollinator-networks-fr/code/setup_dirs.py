import os
import sys
from pathlib import Path

def main():
    """
    Creates the required directory structure for the project.
    
    Directories created:
    - code/
    - data/raw/
    - data/processed/
    - tests/
    - docs/
    - results/
    
    Also creates __init__.py files to initialize Python packages where needed.
    """
    # Get the project root (parent of code/)
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent
    
    # Define relative paths for required directories
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "tests",
        "docs",
        "results"
    ]
    
    # Create directories
    created_dirs = []
    for dir_path in directories:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        created_dirs.append(str(full_path))
        print(f"Created directory: {full_path}")
    
    # Create __init__.py files for Python packages
    init_files = [
        "code/__init__.py",
        "tests/__init__.py",
        "code/utils/__init__.py"
    ]
    
    created_init_files = []
    for init_path in init_files:
        full_path = project_root / init_path
        # Ensure parent directory exists
        full_path.parent.mkdir(parents=True, exist_ok=True)
        # Create empty __init__.py file
        full_path.touch(exist_ok=True)
        created_init_files.append(str(full_path))
        print(f"Created package initializer: {full_path}")
    
    print(f"\nSuccessfully created {len(created_dirs)} directories and {len(created_init_files)} package initializers.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
