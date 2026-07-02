"""
Setup script to create the directory structure for the avian song variation project.
This script creates the necessary folders under the project root as defined in the plan.
"""
import os
import sys
from pathlib import Path

def main():
    # Define the base directories relative to the current working directory (project root)
    # The task specifies: projects/PROJ-334..., data/, code/, tests/
    # We assume the script is run from the project root.
    
    base_dirs = [
        "projects/PROJ-334-predicting-avian-song-variation-with-cli",
        "data",
        "code",
        "tests"
    ]

    # Also create the standard subdirectories for data as per Phase 2 (T004) anticipation
    # and best practices, though strictly T001a asks for the top level.
    # We will stick strictly to T001a requirements for the top level, 
    # but ensure 'data' exists so subsequent tasks can run.
    
    created_count = 0
    for dir_path in base_dirs:
        path = Path(dir_path)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {path}")
            created_count += 1
        else:
            print(f"Directory already exists: {path}")

    # Create specific subdirectories for data structure (data/raw, data/processed)
    # as these are standard and often required immediately by ingestion tasks (T004 context)
    data_subdirs = [
        "data/raw",
        "data/processed",
        "data/external"
    ]
    
    for dir_path in data_subdirs:
        path = Path(dir_path)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {path}")
            created_count += 1
        else:
            print(f"Directory already exists: {path}")

    print(f"Setup complete. {created_count} new directories created.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
