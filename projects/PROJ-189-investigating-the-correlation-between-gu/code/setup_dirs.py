"""
Script to create the required project directory structure for PROJ-189.
This satisfies task T001b.
"""
import os
from pathlib import Path

def main():
    # Determine the project root relative to this script's location
    # The script is in code/, so root is one level up
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent
    
    # Define the required subdirectories relative to project root
    # Per task description: data/raw, data/processed, data/models, code, code/utils, 
    # tests, tests/contract, tests/integration, tests/unit, docs
    # Note: 'code' and 'code/utils' already exist, but we ensure them anyway.
    
    dirs_to_create = [
        "data/raw",
        "data/processed",
        "data/models",
        "code",
        "code/utils",
        "tests",
        "tests/contract",
        "tests/integration",
        "tests/unit",
        "docs"
    ]

    created_count = 0
    for dir_rel in dirs_to_create:
        full_path = project_root / dir_rel
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")

    print(f"\nDirectory creation complete. Created {created_count} new directories.")
    print(f"Project root: {project_root}")

if __name__ == "__main__":
    main()