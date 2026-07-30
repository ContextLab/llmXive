"""
Script to initialize the project directory structure for PROJ-240.
Creates required root directories and subdirectories as per the specification.
"""
import os
import sys
from pathlib import Path

def main():
    # Define the project root based on the task requirement
    project_root = Path("projects/PROJ-240-predicting-the-impact-of-cold-work-on-re")
    
    # Ensure the project root exists
    project_root.mkdir(parents=True, exist_ok=True)
    
    # Define the directories to create
    directories = [
        "code",
        "tests",
        "data",
        "artifacts",
        # Subdirectories for Phase 1 & 2
        "data/raw",
        "data/processed",
        "data/split",
        # Subdirectories for Phase 1 & 3
        "artifacts/models",
        "artifacts/reports",
        "artifacts/figures",
    ]
    
    created_count = 0
    
    for dir_name in directories:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")
    
    # Create __init__.py files to make directories valid Python packages
    # and to satisfy the "project scaffolding" aspect of T001/T005
    init_files = [
        project_root / "code" / "__init__.py",
        project_root / "tests" / "__init__.py",
        project_root / "data" / "__init__.py",
        project_root / "artifacts" / "__init__.py",
    ]
    
    for init_file in init_files:
        # Ensure parent directory exists before writing file
        init_file.parent.mkdir(parents=True, exist_ok=True)
        if not init_file.exists():
            init_file.write_text('"""Project module."""\n')
            print(f"Created init file: {init_file}")
        else:
            print(f"Init file already exists: {init_file}")

    print(f"\nSetup complete. Created {created_count} new directories.")
    return 0

if __name__ == "__main__":
    sys.exit(main())