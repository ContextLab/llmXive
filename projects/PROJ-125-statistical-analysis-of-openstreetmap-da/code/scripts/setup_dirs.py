"""
Setup script to create the project directory structure.

This script ensures that all necessary directories for the project
exist before any data processing or analysis begins.
"""
import os
import sys
from pathlib import Path

def main():
    """Create the standard project directory structure."""
    # Define the project root (assumed to be the parent of the code/ directory)
    # If this script is run from code/scripts/, the root is two levels up.
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent

    # Define the directory structure to create
    directories = [
        "code",
        "data",
        "tests",
        "docs",
        "data/raw",
        "data/processed",
        "data/results",
        "data/figures",
        "code/models",
        "code/utils",
        "code/scripts",
        "code/reports",
        "tests/unit",
        "tests/integration",
        "specs",
    ]

    created_count = 0
    skipped_count = 0

    print(f"Project Root: {project_root}")
    
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path.relative_to(project_root)}")
            created_count += 1
        else:
            # Check if it's actually a directory
            if full_path.is_dir():
                skipped_count += 1
            else:
                print(f"Warning: Path exists but is not a directory: {full_path}")

    print(f"\nSetup complete. Created {created_count} new directories, skipped {skipped_count} existing.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
