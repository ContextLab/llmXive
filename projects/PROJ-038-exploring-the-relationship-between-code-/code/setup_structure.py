"""
Script to initialize the project directory structure for PROJ-038.
Creates the required folders for source code, tests, data (raw, processed, results),
and specifications as defined in tasks.md (Task T001a).
"""
import os
from pathlib import Path

def main():
    base_dir = Path(__file__).parent

    # Define the required directory structure relative to the code/ root
    # Note: specs/ is created at the project root level based on the task description
    # but we will create it relative to where this script runs if needed,
    # or assume the script is run from the project root.
    # To be safe and compliant with "Stay inside the project tree", we create
    # everything relative to the script's parent (project root).
    
    project_root = base_dir.parent if base_dir.name == "code" else base_dir

    # Paths to create
    # 1. code/ tree
    code_dirs = [
        "code",
        "code/src",
        "code/tests",
        "code/data/raw",
        "code/data/processed",
        "code/data/results",
    ]

    # 2. specs/ tree
    specs_dirs = [
        "specs/001-code-complexity-bug-prediction",
    ]

    all_dirs = code_dirs + specs_dirs

    created_count = 0
    for dir_path in all_dirs:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created: {full_path}")
            created_count += 1
        else:
            # Ensure it is actually a directory
            if full_path.is_dir():
                print(f"Exists: {full_path}")
            else:
                raise RuntimeError(f"Path exists but is not a directory: {full_path}")

    print(f"\nDirectory structure initialization complete. Created {created_count} new directories.")

if __name__ == "__main__":
    main()
