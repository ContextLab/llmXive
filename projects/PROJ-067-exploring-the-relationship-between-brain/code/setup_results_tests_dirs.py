"""
Task T010: Initialize `results/` directory structure (`plots/`) and `tests/` directory structure (`contract/`, `unit/`).

This script creates the necessary directory tree for storing analysis outputs
and test artifacts as defined in the project plan.
"""
import os
from pathlib import Path

def main():
    root = Path(__file__).resolve().parent.parent
    
    # Define the directories to create relative to project root
    dirs_to_create = [
        "results/plots",
        "tests/contract",
        "tests/unit"
    ]
    
    created_count = 0
    for dir_path in dirs_to_create:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    # Create __init__.py files to ensure they are recognized as packages
    init_files = [
        root / "tests" / "__init__.py",
        root / "tests" / "contract" / "__init__.py",
        root / "tests" / "unit" / "__init__.py"
    ]
    
    for init_file in init_files:
        if not init_file.exists():
            init_file.touch()
            print(f"Created placeholder: {init_file}")
        else:
            print(f"Placeholder already exists: {init_file}")
    
    print(f"T010 Initialization complete. {created_count} new directories created.")

if __name__ == "__main__":
    main()
