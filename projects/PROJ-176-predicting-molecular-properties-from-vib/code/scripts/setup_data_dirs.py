"""
Script to initialize the project's data directory structure.
Creates raw/, preprocessed/, and external/ subdirectories under data/.
"""
import os
from pathlib import Path

def main():
    """
    Creates the required data directory structure.
    """
    # Define the base data directory relative to the project root
    # Assuming this script runs from code/scripts/, we go up two levels
    project_root = Path(__file__).resolve().parent.parent.parent
    data_dir = project_root / "data"

    # Define the required subdirectories
    subdirs = ["raw", "preprocessed", "external"]

    print(f"Initializing data directory structure at: {data_dir}")

    created_count = 0
    for subdir_name in subdirs:
        subdir_path = data_dir / subdir_name
        if not subdir_path.exists():
            subdir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {subdir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {subdir_path}")

    if created_count > 0:
        print(f"Successfully created {created_count} new directory(ies).")
    else:
        print("All required directories already exist.")

    # Verify structure
    print("\nVerification:")
    for subdir_name in subdirs:
        subdir_path = data_dir / subdir_name
        if subdir_path.exists() and subdir_path.is_dir():
            print(f"  [OK] {subdir_path}")
        else:
            print(f"  [FAIL] {subdir_path} missing or not a directory")

    return 0

if __name__ == "__main__":
    exit(main())