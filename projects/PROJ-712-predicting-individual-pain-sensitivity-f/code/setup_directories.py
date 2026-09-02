import os
import sys
from pathlib import Path

def main():
    """
    Creates the required directory structure for project PROJ-712.
    
    Creates:
    - projects/PROJ-712-predicting-individual-pain-sensitivity-f/data/raw/
    - projects/PROJ-712-predicting-individual-pain-sensitivity-f/data/processed/
    - projects/PROJ-712-predicting-individual-pain-sensitivity-f/artifacts/
    - projects/PROJ-712-predicting-individual-pain-sensitivity-f/state/
    - projects/PROJ-712-predicting-individual-pain-sensitivity-f/code/
    - projects/PROJ-712-predicting-individual-pain-sensitivity-f/tests/
    
    This script ensures the directory tree exists on disk before other
    pipeline stages attempt to write data or artifacts.
    """
    # Define the project root relative to the current working directory
    project_root = Path("projects/PROJ-712-predicting-individual-pain-sensitivity-f")
    
    # Define the directories to create based on T001a, T001b, T001c
    directories = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "artifacts",
        project_root / "state",
        project_root / "code",
        project_root / "tests",
    ]
    
    created_count = 0
    for directory in directories:
        # Create the directory and any necessary parents
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")
        created_count += 1
    
    print(f"Successfully created {created_count} directories.")
    
    # Verify existence for robustness
    all_exist = all(d.exists() and d.is_dir() for d in directories)
    if not all_exist:
        raise RuntimeError("Failed to create all required directories.")

if __name__ == "__main__":
    main()
