"""
Script to create the project directory structure for the plant stress response pipeline.
This script ensures all required directories exist before data ingestion and modeling begin.
"""
import os
import sys
from pathlib import Path

# Define the project root relative to this script's location or current working directory
# Assuming this script is run from the project root or code/ directory
PROJECT_ROOT = Path(__file__).parent.parent if (Path(__file__).parent / "code").exists() else Path.cwd()

# Required directories relative to PROJECT_ROOT
REQUIRED_DIRS = [
    "code/data_ingestion",
    "code/modeling",
    "code/reporting",
    "code/utils",
    "tests",
    "data/raw",
    "data/processed",
    "results",
    "logs",
    "docs"
]

def main():
    """
    Creates all required directories if they do not already exist.
    Prints status for each directory and exits with code 0 on success.
    """
    created_count = 0
    skipped_count = 0
    failed_count = 0

    print(f"Creating project directory structure at: {PROJECT_ROOT}")

    for dir_path in REQUIRED_DIRS:
        full_path = PROJECT_ROOT / dir_path
        try:
            if not full_path.exists():
                full_path.mkdir(parents=True, exist_ok=True)
                print(f"  [CREATED] {dir_path}")
                created_count += 1
            else:
                # Verify it is a directory
                if full_path.is_dir():
                    print(f"  [EXISTS]  {dir_path}")
                    skipped_count += 1
                else:
                    print(f"  [ERROR]   {dir_path} exists but is not a directory!")
                    failed_count += 1
        except PermissionError:
            print(f"  [ERROR]   Permission denied creating {dir_path}")
            failed_count += 1
        except Exception as e:
            print(f"  [ERROR]   Failed to create {dir_path}: {e}")
            failed_count += 1

    print("-" * 40)
    print(f"Summary: {created_count} created, {skipped_count} existed, {failed_count} failed")

    if failed_count > 0:
        print("ERROR: Some directories could not be created.")
        sys.exit(1)
    else:
        print("SUCCESS: Directory structure verified.")
        sys.exit(0)

if __name__ == "__main__":
    main()