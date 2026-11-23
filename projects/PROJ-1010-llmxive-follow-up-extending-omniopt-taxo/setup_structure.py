"""
Script to initialize the project directory structure for PROJ-1010.
This script creates the required folders and empty marker files as per T001a.
"""
import os
import sys
from pathlib import Path

def create_structure():
    # Define the project root relative to where this script is run from
    # The script is expected to be run from the project root or code directory,
    # but the paths in tasks.md are relative to the project root.
    # We assume the script is executed from the directory containing 'projects/'.
    
    project_root = Path("projects/PROJ-1010-llmxive-follow-up-extending-omniopt-taxo")
    
    # Directories to create
    directories = [
        "code",
        "data",
        "tests",
        "state",
        # Subdirectories for code
        "code/utils",
        "code/data",
        "code/analysis",
        # Subdirectories for tests
        "tests/unit",
        "tests/integration",
        # Data subdirectories (often needed early)
        "data/raw",
        "data/processed",
        "data/figures",
    ]

    created_count = 0
    skipped_count = 0

    print(f"Initializing structure for project: {project_root}")

    for dir_path in directories:
        full_path = project_root / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"  [OK] Created: {full_path}")
            created_count += 1
        except OSError as e:
            print(f"  [FAIL] Could not create {full_path}: {e}")
            # Continue rather than failing immediately if it's just a permission issue on one dir

    # Create empty marker files if they don't exist to ensure the directories are recognized
    # as part of the project structure (optional but good practice)
    marker_files = [
        project_root / "README.md",
        project_root / "data" / ".gitkeep",
        project_root / "tests" / ".gitkeep",
        project_root / "state" / ".gitkeep",
    ]

    for file_path in marker_files:
        if not file_path.exists():
            try:
                file_path.touch()
                print(f"  [OK] Created marker: {file_path}")
                created_count += 1
            except OSError as e:
                print(f"  [WARN] Could not create marker {file_path}: {e}")
        else:
            skipped_count += 1

    print(f"\nStructure initialization complete.")
    print(f"  Directories created: {created_count}")
    print(f"  Files skipped (already exist): {skipped_count}")
    
    return True

if __name__ == "__main__":
    success = create_structure()
    sys.exit(0 if success else 1)