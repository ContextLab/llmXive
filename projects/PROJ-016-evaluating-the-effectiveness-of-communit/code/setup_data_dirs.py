import os
import sys
from pathlib import Path

def main():
    """
    Setup data directories (`data/raw/`, `data/processed/`) and output directories (`docs/output/`).
    This script ensures the required directory structure exists for the project.
    """
    # Define the project root (assumed to be the parent of the 'code' directory)
    # If this script is run from 'code/', we need to go up one level
    project_root = Path(__file__).resolve().parent.parent
    
    directories = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "docs" / "output",
        # Ensure logs directory exists as well for T005 compatibility
        project_root / "logs",
    ]

    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory}")
            created_count += 1
        else:
            print(f"Directory already exists: {directory}")

    if created_count > 0:
        print(f"Successfully created {created_count} new directory/directories.")
    else:
        print("All required directories already existed.")

    return 0

if __name__ == "__main__":
    sys.exit(main())
