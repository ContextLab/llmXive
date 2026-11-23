"""
Script to initialize the project's data directory structure.
Creates 'data/raw' and 'data/processed' directories as required by T001d.
"""
import os
from pathlib import Path

def main():
    """
    Creates the required data subdirectories.
    """
    # Define the project root (assuming this script is in code/ or project root)
    # We look for 'data' relative to the script's location or current working directory
    project_root = Path(__file__).resolve().parent.parent
    data_root = project_root / "data"

    # Ensure the root data directory exists
    data_root.mkdir(parents=True, exist_ok=True)

    # Define required subdirectories per T001d
    directories = [
        data_root / "raw",
        data_root / "processed",
    ]

    created = []
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            created.append(str(directory))
            print(f"Created directory: {directory}")
        else:
            print(f"Directory already exists: {directory}")

    if not created:
        print("All required data directories already exist.")
    else:
        print(f"Successfully created {len(created)} data directory/directories.")

    return 0

if __name__ == "__main__":
    exit(main())