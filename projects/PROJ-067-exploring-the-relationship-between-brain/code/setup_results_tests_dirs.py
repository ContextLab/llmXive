"""
Task T010: Initialize `results/` directory structure (`plots/`) 
and `tests/` directory structure (`contract/`, `unit/`).

This script ensures the required directory hierarchy exists at the project root.
"""
import os
from pathlib import Path

def main():
    # Determine project root (assuming this script is in code/, root is parent)
    project_root = Path(__file__).resolve().parent.parent
    
    # Define directories to create
    directories = [
        project_root / "results" / "plots",
        project_root / "tests" / "contract",
        project_root / "tests" / "unit",
    ]
    
    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory}")
            created_count += 1
        else:
            print(f"Directory exists: {directory}")
    
    # Create placeholder __init__.py files to ensure test discovery works
    # and to mark directories as Python packages if needed
    init_files = [
        project_root / "tests" / "__init__.py",
        project_root / "tests" / "contract" / "__init__.py",
        project_root / "tests" / "unit" / "__init__.py",
        project_root / "results" / "__init__.py",
        project_root / "results" / "plots" / "__init__.py",
    ]
    
    for init_file in init_files:
        if not init_file.exists():
            init_file.touch()
            print(f"Created placeholder: {init_file}")
    
    print(f"T010 Complete: Created {created_count} new directories.")

if __name__ == "__main__":
    main()