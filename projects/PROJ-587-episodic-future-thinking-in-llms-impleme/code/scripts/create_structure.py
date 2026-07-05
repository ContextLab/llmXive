"""
Script to initialize the project directory structure for PROJ-587.
This script creates the necessary folders for data, models, services, experiments,
validation, utils, and tests as defined in the project plan.
"""
import os
from pathlib import Path

def main():
    # Define the project root relative to the script location or current working directory
    # The task specifies paths relative to project root, assuming this runs from project root
    project_root = Path(".")
    code_dir = project_root / "code"
    
    # Define the directory structure to create
    dirs_to_create = [
        "data/raw",
        "data/processed",
        "models",
        "services",
        "experiments",
        "validation",
        "utils",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "scripts"
    ]
    
    created_count = 0
    for dir_path in dirs_to_create:
        full_path = code_dir / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created: {full_path}")
            created_count += 1
        else:
            print(f"Exists: {full_path}")
    
    print(f"\nDirectory initialization complete. Created {created_count} new directories.")
    print(f"Base directory: {code_dir.resolve()}")

if __name__ == "__main__":
    main()
