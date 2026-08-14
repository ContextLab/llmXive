import os
import sys
from pathlib import Path

def main():
    """
    Create the directory structure for project PROJ-150.
    This script ensures that the required directories exist relative to the project root.
    """
    # Determine project root. Assuming this script is in code/, root is parent.
    # If running as python code/setup_dirs.py, __file__ is code/setup_dirs.py
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent

    project_name = "PROJ-150-detecting-statistical-power-drift-in-rep"
    project_dir = project_root / project_name

    # Define subdirectories as per task requirement
    subdirs = [
        "data/raw",
        "data/derived",
        "code",
        "tests",
        "results",
        "state"
    ]

    created_dirs = []
    for subdir in subdirs:
        dir_path = project_dir / subdir
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(dir_path.relative_to(project_root)))
        else:
            print(f"Directory exists: {dir_path}")

    if created_dirs:
        print(f"Created directories for {project_name}:")
        for d in created_dirs:
            print(f"  - {d}")
    else:
        print(f"All directories for {project_name} already exist.")

    # Verify structure
    print(f"\nVerifying structure at: {project_dir}")
    for subdir in subdirs:
        target = project_dir / subdir
        if target.exists() and target.is_dir():
            print(f"  [OK] {subdir}")
        else:
            print(f"  [FAIL] {subdir} missing")
            sys.exit(1)

if __name__ == "__main__":
    main()
