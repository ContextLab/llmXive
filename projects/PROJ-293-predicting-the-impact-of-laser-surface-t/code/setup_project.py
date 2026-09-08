"""
Script to create the project directory structure as defined in T001.
Creates: code/, data/, tests/, state/, models/, data/raw/, data/processed/, reports/
"""
import os
from pathlib import Path

def main():
    # Define the base directory (project root)
    base_dir = Path(__file__).resolve().parent.parent

    # Define the directories to create based on the task requirements
    # Note: 'code', 'data', 'tests', 'state', 'reports', 'models' are top level
    # 'data/raw' and 'data/processed' are subdirectories of 'data'
    directories = [
        "code",
        "data",
        "tests",
        "state",
        "reports",
        "models",
        "data/raw",
        "data/processed"
    ]

    created_dirs = []
    skipped_dirs = []

    for dir_path in directories:
        full_path = base_dir / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(full_path))
        except PermissionError:
            print(f"Permission denied creating: {full_path}")
        except Exception as e:
            print(f"Error creating {full_path}: {e}")

    print("Project structure setup complete.")
    print(f"Created/Verified directories: {len(created_dirs)}")
    for d in created_dirs:
        print(f"  - {d}")

    if skipped_dirs:
        print(f"Skipped (already exist or errors): {len(skipped_dirs)}")
        for d in skipped_dirs:
            print(f"  - {d}")

if __name__ == "__main__":
    main()