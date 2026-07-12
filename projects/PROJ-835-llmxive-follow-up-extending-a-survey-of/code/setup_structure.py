import os
import sys
from pathlib import Path

def create_structure():
    """
    Creates the project directory structure as defined in the implementation plan.
    
    Required directories:
    - src/ (source code)
    - src/data/
    - src/models/
    - src/utils/
    - tests/
    - tests/contract/
    - tests/integration/
    - data/
    - models/
    - results/
    - state/
    - state/projects/
    """
    # Define the project root relative to this script's location
    # The script is in code/, so root is parent of code/
    script_dir = Path(__file__).parent.resolve()
    project_root = script_dir.parent
    
    # Define all required directories relative to project root
    directories = [
        "src",
        "src/data",
        "src/models",
        "src/utils",
        "tests",
        "tests/contract",
        "tests/integration",
        "data",
        "models",
        "results",
        "state",
        "state/projects",
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    # Create __init__.py files in src subdirectories to make them proper packages
    init_files = [
        "src/__init__.py",
        "src/data/__init__.py",
        "src/models/__init__.py",
        "src/utils/__init__.py",
        "tests/__init__.py",
        "tests/contract/__init__.py",
        "tests/integration/__init__.py",
    ]
    
    for init_path in init_files:
        full_path = project_root / init_path
        if not full_path.exists():
            full_path.touch()
            print(f"Created init file: {full_path}")
        else:
            print(f"Init file already exists: {full_path}")
    
    print(f"\nProject structure setup complete. Created {created_count} new directories.")
    return True

if __name__ == "__main__":
    create_structure()