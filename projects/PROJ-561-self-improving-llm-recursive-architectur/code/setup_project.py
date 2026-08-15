import os
import sys
from pathlib import Path

def create_project_structure():
    """
    Creates the required project directory structure and initializes __init__.py files.
    
    Directories created:
    - code/
    - data/raw/
    - data/processed/
    - results/
    - specs/
    - tests/
    - tests/unit/
    - tests/integration/
    
    Also creates __init__.py in each directory to make them Python packages.
    """
    # Define the root directory (current working directory or project root)
    root = Path(".")
    
    # Define all required directories relative to root
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "results",
        "specs",
        "tests",
        "tests/unit",
        "tests/integration"
    ]
    
    created_dirs = []
    created_files = []
    
    for dir_path in directories:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(dir_path)
            print(f"Created directory: {dir_path}")
        
        # Create __init__.py in each directory
        init_file = full_path / "__init__.py"
        if not init_file.exists():
            init_file.touch()
            created_files.append(str(init_file))
            print(f"Created __init__.py: {init_file}")
        else:
            print(f"__init__.py already exists: {init_file}")
    
    # Summary
    print(f"\nProject structure setup complete.")
    print(f"Directories created: {len(created_dirs)}")
    print(f"__init__.py files created: {len(created_files)}")
    
    return {
        "directories_created": created_dirs,
        "init_files_created": created_files,
        "total_directories": len(directories),
        "total_init_files": len(directories)
    }

if __name__ == "__main__":
    result = create_project_structure()
    print("\nSummary:")
    print(f"  Total directories: {result['total_directories']}")
    print(f"  Total __init__.py files: {result['total_init_files']}")
