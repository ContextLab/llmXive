import os
import sys
from pathlib import Path

def main():
    """
    Creates the directory structure for the avian foraging behavior project.
    
    Creates the following subdirectories under code/:
    - data
    - models
    - viz
    - notebooks
    - utils
    - tests
    
    Also creates __init__.py files in each directory to make them Python packages.
    """
    # Get the project root directory (parent of 'code')
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent
    
    # Define the base code directory
    code_dir = project_root / "code"
    
    # Subdirectories to create
    subdirs = [
        "data",
        "models", 
        "viz",
        "notebooks",
        "utils",
        "tests"
    ]
    
    # Create directories
    print(f"Creating directory structure in: {code_dir}")
    for subdir in subdirs:
        dir_path = code_dir / subdir
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"  Created: {dir_path}")
        
        # Create __init__.py to make it a Python package
        init_file = dir_path / "__init__.py"
        init_file.touch()
        print(f"  Created: {init_file}")
    
    # Create data subdirectories
    data_subdirs = [
        "data/raw",
        "data/processed",
        "data/interim"
    ]
    for subdir in data_subdirs:
        dir_path = code_dir / subdir
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"  Created: {dir_path}")
        init_file = dir_path / "__init__.py"
        init_file.touch()
        print(f"  Created: {init_file}")
    
    print("\nDirectory structure created successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(main())