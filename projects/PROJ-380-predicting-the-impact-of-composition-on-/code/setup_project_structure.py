import os
from pathlib import Path

def create_structure():
    """
    Creates the project directory structure as per the implementation plan.
    Creates: code/, data/, tests/, docs/, state/, artifacts/
    """
    root = Path.cwd()
    
    # Define the required directories relative to the project root
    directories = [
        "code",
        "code/data",
        "code/models",
        "code/utils",
        "code/viz",
        "data",
        "data/raw",
        "data/processed",
        "data/artifacts",
        "tests",
        "tests/unit",
        "tests/integration",
        "docs",
        "specs",
        "state",
        "state/projects",
        "artifacts",
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")
    
    # Create placeholder __init__.py files in Python package directories
    python_dirs = [
        "code",
        "code/data",
        "code/models",
        "code/utils",
        "code/viz",
        "tests",
        "tests/unit",
        "tests/integration",
    ]
    
    for dir_path in python_dirs:
        init_file = root / dir_path / "__init__.py"
        if not init_file.exists():
            init_file.touch()
            print(f"Created placeholder: {init_file}")
    
    print(f"\nProject structure creation complete. {created_count} new directories created.")

if __name__ == "__main__":
    create_structure()
