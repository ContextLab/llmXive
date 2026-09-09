import os
import sys
from pathlib import Path

def main():
    """
    Create the required project directory structure for PROJ-379.
    Creates: data/raw, data/processed, code, tests, docs
    """
    # Define the project root relative to the current working directory
    # The task specifies creating these in projects/PROJ-379-predicting-molecular-excitation-waveleng/
    # We assume the script is run from the repository root or the project root.
    # To be safe, we create the structure relative to the script's location if not absolute.
    
    base_dir = Path(__file__).resolve().parent.parent
    project_name = "PROJ-379-predicting-molecular-excitation-waveleng"
    
    # If we are already inside the project folder, base_dir might be the project root.
    # We check if the project folder exists inside base_dir to determine the correct root.
    if (base_dir / project_name).exists():
        project_root = base_dir / project_name
    else:
        # Assume current directory is the project root or we are running from within the project folder
        # If the script is in code/, parent is project root.
        project_root = base_dir

    # Define required directories
    dirs_to_create = [
        "data/raw",
        "data/processed",
        "code",
        "tests",
        "docs"
    ]

    created_count = 0
    for dir_path in dirs_to_create:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")

    print(f"Project structure verification complete. Created {created_count} new directories.")
    print(f"Project root: {project_root}")

    # Verify the structure exists by listing the created paths
    print("\nVerified Directory Structure:")
    for dir_path in dirs_to_create:
        full_path = project_root / dir_path
        if full_path.exists():
            print(f"  [OK] {full_path}")
        else:
            print(f"  [FAIL] {full_path}")
            sys.exit(1)

if __name__ == "__main__":
    main()