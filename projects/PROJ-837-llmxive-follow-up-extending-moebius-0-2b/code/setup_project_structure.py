import os
from pathlib import Path

def create_project_structure():
    """
    Creates the full project directory structure and initializes Python packages.
    
    This function creates the following hierarchy:
    - code/ (data, models, training, eval, utils)
    - data/ (raw, processed, annotations, results)
    - specs/001-llmxive-moebius-dynamic
    - tests/ (unit, integration)
    - docs
    - paper
    - state/projects
    
    And adds __init__.py to all Python package directories.
    """
    # Define the base directories to create
    base_dirs = [
        "code/data",
        "code/models",
        "code/training",
        "code/eval",
        "code/utils",
        "data/raw",
        "data/processed",
        "data/annotations",
        "data/results",
        "specs/001-llmxive-moebius-dynamic",
        "tests/unit",
        "tests/integration",
        "docs",
        "paper",
        "state/projects",
    ]
    
    # Create directories
    for dir_path in base_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")
    
    # Define Python package directories that need __init__.py
    python_package_dirs = [
        "code",
        "code/data",
        "code/models",
        "code/training",
        "code/eval",
        "code/utils",
        "tests",
        "tests/unit",
        "tests/integration",
    ]
    
    # Create __init__.py files
    for dir_path in python_package_dirs:
        init_file = Path(dir_path) / "__init__.py"
        init_file.touch(exist_ok=True)
        print(f"Created __init__.py: {init_file}")
    
    print("\nProject structure creation complete.")
    print("Directories created:")
    for dir_path in base_dirs:
        print(f"  - {dir_path}")
    print("\nPython packages initialized:")
    for dir_path in python_package_dirs:
        print(f"  - {dir_path}/")

if __name__ == "__main__":
    create_project_structure()