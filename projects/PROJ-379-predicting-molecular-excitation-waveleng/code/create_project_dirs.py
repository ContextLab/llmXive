import os
import sys
from pathlib import Path

def main():
    """
    Create the required project directory structure for PROJ-379.
    
    Creates:
    - data/raw
    - data/processed
    - code
    - tests
    - docs
    
    All relative to the project root: projects/PROJ-379-predicting-molecular-excitation-waveleng/
    """
    # Determine project root. If run from within the project, use current dir.
    # Expected to be run from the project root.
    project_root = Path.cwd()
    
    # Define the specific project directory name to ensure we are in the right place
    # or create it if we are running from a parent.
    # However, standard practice is to run this from the project root.
    # We will create the subdirectories relative to the current working directory.
    
    subdirs = [
        "data/raw",
        "data/processed",
        "code",
        "tests",
        "docs"
    ]
    
    created_count = 0
    for subdir in subdirs:
        dir_path = project_root / subdir
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")
    
    # Create empty checksums.txt as required by T004 context (often paired with dir creation)
    # Although T004 is a separate task, the directory structure often implies the need for this file.
    # The task T001a specifically asks for directories, but T004 is marked as missing/invalid in the
    # rejection notes. To be safe and ensure the structure is complete for the pipeline,
    # we will ensure the data directory is ready. We will NOT create checksums.txt here
    # as that is T004's specific responsibility, but we ensure the parent 'data' exists.
    
    if created_count > 0:
        print(f"Successfully created {created_count} directories.")
    else:
        print("All directories already existed.")

if __name__ == "__main__":
    main()