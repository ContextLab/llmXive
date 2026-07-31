"""
Setup script to initialize the project directory structure.
Creates standard directories for code, data (raw, interim, processed, results), and tests.
"""
import os
import sys
from pathlib import Path

def main():
    # Define the project root relative to where this script is run
    # Assuming the script is run from the project root: projects/PROJ-407-predicting-herbivore-resistance-fr/
    project_root = Path.cwd()
    
    directories = [
        "code",
        "data/raw",
        "data/interim",
        "data/processed",
        "data/results",
        "tests/unit",
        "tests/integration",
        "tests/contract"
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"Project structure initialization complete. {created_count} new directories created.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
