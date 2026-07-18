import os
import sys
from pathlib import Path

def create_structure():
    """
    Creates the required project directory structure for llmXive project PROJ-144.
    
    Directories created:
    - code/
    - data/raw
    - data/processed
    - tests/
    - state/
    - contracts/
    - results/
    - figures/
    """
    # Define the base directory (project root)
    base_dir = Path(__file__).resolve().parent.parent
    
    # Define the directories to create based on the task requirements and standard structure
    directories = [
        base_dir / "code",
        base_dir / "data" / "raw",
        base_dir / "data" / "processed",
        base_dir / "tests",
        base_dir / "state",
        base_dir / "contracts",
        base_dir / "results",
        base_dir / "figures",
        # Subdirectories for code organization
        base_dir / "code" / "data",
        base_dir / "code" / "modeling",
        base_dir / "code" / "utils",
        base_dir / "tests" / "unit",
        base_dir / "tests" / "integration",
    ]
    
    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory}")
            created_count += 1
        else:
            print(f"Directory already exists: {directory}")
    
    # Create __init__.py files to make directories into Python packages
    init_files = [
        base_dir / "code" / "__init__.py",
        base_dir / "code" / "data" / "__init__.py",
        base_dir / "code" / "modeling" / "__init__.py",
        base_dir / "code" / "utils" / "__init__.py",
        base_dir / "tests" / "__init__.py",
        base_dir / "tests" / "unit" / "__init__.py",
        base_dir / "tests" / "integration" / "__init__.py",
    ]
    
    for init_file in init_files:
        if not init_file.exists():
            init_file.touch()
            print(f"Created init file: {init_file}")
        else:
            print(f"Init file already exists: {init_file}")
    
    print(f"\nProject structure setup complete. Created {created_count} new directories.")
    return True

if __name__ == "__main__":
    create_structure()
