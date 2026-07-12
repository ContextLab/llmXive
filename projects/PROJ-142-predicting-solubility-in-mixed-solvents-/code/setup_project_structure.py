"""
Script to initialize the project directory structure for the solubility prediction pipeline.
Creates all required directories as specified in T001.
"""
import os
import sys
from pathlib import Path

def main():
    # Define the project root (assuming this script runs from the project root or code/)
    # If run from code/, we need to go up one level to create the structure relative to root
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent if current_file.name == "setup_project_structure.py" else current_file.parent

    # Ensure we are working with the correct root if the script is placed in code/
    if "code" in str(current_file):
        project_root = current_file.parent.parent
    else:
        project_root = current_file.parent

    # Define the required directory structure
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/artifacts",
        "tests",
        "specs/001-predicting-solubility-in-mixed-solvents/contracts"
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

    if created_count == 0:
        print("All required directories already exist.")
    else:
        print(f"Successfully created {created_count} new directories.")

    return 0

if __name__ == "__main__":
    sys.exit(main())