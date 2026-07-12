import os
import sys
from pathlib import Path

def main():
    """
    Creates the required project directory structure for the solubility prediction pipeline.
    Ensures all necessary folders exist before data processing or model training begins.
    """
    # Define the project root relative to the script location
    # Assuming this script is in code/, root is parent
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent

    # Define all required directories
    directories = [
        project_root / "code",
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "artifacts",
        project_root / "tests",
        project_root / "specs" / "001-predicting-solubility-in-mixed-solvents" / "contracts",
    ]

    created_count = 0
    for dir_path in directories:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            # Verify it is actually a directory, not a file
            if not dir_path.is_dir():
                raise NotADirectoryError(f"Path exists but is not a directory: {dir_path}")

    if created_count == 0:
        print("All required directories already exist.")
    else:
        print(f"Successfully created {created_count} new directories.")

if __name__ == "__main__":
    main()
