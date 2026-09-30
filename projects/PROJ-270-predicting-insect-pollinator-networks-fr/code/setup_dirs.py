"""
Script to initialize the project directory structure.
This script creates the required directories for the llmXive project.
"""
import os
import sys
from pathlib import Path

def main():
    """Create the standard project directory structure."""
    project_root = Path(__file__).resolve().parent.parent
    
    # Define the directories to create relative to the project root
    # Based on T001a requirements: code/, data/raw/, data/processed/, tests/, docs/, results/
    # Note: 'code/' already exists as the parent of this script, but we ensure it and subdirs
    
    dirs_to_create = [
        "code",
        "data/raw",
        "data/processed",
        "tests",
        "docs",
        "results",
        "figures",  # Often needed for outputs, good practice to include
        "results/metrics",
        "results/reports",
    ]

    created_count = 0
    for dir_path in dirs_to_create:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path.relative_to(project_root)}")
            created_count += 1
        else:
            # Ensure it's actually a directory
            if not full_path.is_dir():
                raise ValueError(f"Path exists but is not a directory: {full_path}")
            print(f"Directory already exists: {full_path.relative_to(project_root)}")

    if created_count > 0:
        print(f"\nSuccessfully created {created_count} new directories.")
    else:
        print("\nAll required directories already exist.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
