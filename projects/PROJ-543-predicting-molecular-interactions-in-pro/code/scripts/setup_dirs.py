"""
Script to create the project directory structure for PROJ-543.
This script ensures all required folders for code, data, tests, and specs exist.
"""
import os
import sys
from pathlib import Path

def main():
    # Define the project root based on the task description
    # The task specifies paths relative to the project root, but the script
    # is located in code/scripts. We need to construct the full path.
    # The task description implies the project root is 'projects/PROJ-543-predicting-molecular-interactions-in-pro'
    # relative to the current working directory where the script is run.
    
    # To be robust, we assume the script is run from the repository root.
    # We construct the target project directory.
    project_root = Path("projects/PROJ-543-predicting-molecular-interactions-in-pro")
    
    # Define the directories to create as per T001a
    directories = [
        project_root / "code",
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "results",
        project_root / "tests",
        project_root / "specs",
    ]

    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory}")
            created_count += 1
        else:
            print(f"Directory already exists: {directory}")

    if created_count == 0:
        print("All directories already exist. No changes made.")
    else:
        print(f"Successfully created {created_count} directories.")

    # Verify existence for the task requirement (T001a)
    missing = [d for d in directories if not d.exists()]
    if missing:
        print(f"Error: The following directories could not be created: {missing}", file=sys.stderr)
        sys.exit(1)
    
    print("Project directory structure verification complete.")

if __name__ == "__main__":
    main()