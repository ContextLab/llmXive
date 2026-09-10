"""
Project Setup Script for llmXive - PROJ-016
Creates the required directory structure for the project.
"""
import os
import sys
from pathlib import Path

def main():
    """
    Creates the project directory structure as defined in the implementation plan.
    Directories created:
    - code/data
    - code/analysis
    - code/tests
    - data/raw
    - data/processed
    - docs/output
    """
    # Define the base directory (project root)
    # We assume this script runs from the project root or code/
    # We'll resolve relative to the script's location to be safe, then go up one if needed
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent if script_dir.name == "code" else script_dir

    # Define the directories to create
    # Relative to project_root
    directories = [
        "code/data",
        "code/analysis",
        "code/tests",
        "data/raw",
        "data/processed",
        "docs/output"
    ]

    created_count = 0
    skipped_count = 0

    for dir_path in directories:
        full_path = project_root / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            if full_path.is_dir():
                print(f"Created/Verified directory: {full_path}")
                created_count += 1
            else:
                print(f"Error: {full_path} exists but is not a directory")
        except PermissionError:
            print(f"Error: Permission denied creating {full_path}")
        except Exception as e:
            print(f"Error creating {full_path}: {e}")

    print(f"\nSetup complete. Created/Verified {created_count} directories.")
    print(f"Skipped/Existing: {skipped_count}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
