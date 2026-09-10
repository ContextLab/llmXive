"""
Script to create the project directory structure for PROJ-428.
Ensures atomic creation of all required directories using mkdir -p logic.
"""
import os
import sys
from pathlib import Path

def main():
    # Define the project root relative to where this script is located
    # The script is in code/, so root is parent of code/
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent

    # Define required directories relative to project root
    # Based on tasks.md and standard conventions for this project
    dirs_to_create = [
        "data/raw",
        "data/processed",
        "data/results",
        "data/results/figures",
        "state",
        "code/src",
        "code/tests",
        "docs",
        "configs",
        "projects/PROJ-428-evaluating-the-impact-of-outlier-removal",
        "projects/PROJ-428-evaluating-the-impact-of-outlier-removal/data/raw",
        "projects/PROJ-428-evaluating-the-impact-of-outlier-removal/data/processed",
        "projects/PROJ-428-evaluating-the-impact-of-outlier-removal/data/results",
        "projects/PROJ-428-evaluating-the-impact-of-outlier-removal/data/results/figures",
        "projects/PROJ-428-evaluating-the-impact-of-outlier-removal/state",
        "projects/PROJ-428-evaluating-the-impact-of-outlier-removal/code/src",
        "projects/PROJ-428-evaluating-the-impact-of-outlier-removal/code/tests",
        "projects/PROJ-428-evaluating-the-impact-of-outlier-removal/docs",
        "projects/PROJ-428-evaluating-the-impact-of-outlier-removal/configs",
    ]

    created_count = 0
    existing_count = 0

    print(f"Creating project structure at: {project_root}")

    for dir_path in dirs_to_create:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created: {full_path}")
            created_count += 1
        else:
            existing_count += 1

    print(f"\nProject structure setup complete.")
    print(f"  New directories created: {created_count}")
    print(f"  Directories already existing: {existing_count}")

    # Verify critical directories exist
    critical_dirs = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "results",
        project_root / "state",
        project_root / "code" / "src",
        project_root / "code" / "tests",
    ]

    missing = [str(d) for d in critical_dirs if not d.exists()]
    if missing:
        print(f"ERROR: Critical directories missing: {missing}")
        sys.exit(1)

    print("All critical directories verified.")

if __name__ == "__main__":
    main()
