"""
Script to create the root project directory structure for PROJ-356.
This script ensures the existence of the primary code root directory
and its essential subdirectories as defined in the project plan.
"""
import os
from pathlib import Path

def main():
    """Create the required directory structure."""
    # Define the root project path relative to the current working directory
    # The task specifies: projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/
    project_root = Path.cwd()
    target_dir = project_root / "projects" / "PROJ-356-predicting-molecular-toxicity-from-struc" / "code"

    print(f"Ensuring directory exists: {target_dir}")
    target_dir.mkdir(parents=True, exist_ok=True)

    # Create standard subdirectories immediately to ensure the structure is valid
    subdirs = [
        "src",
        "tests",
        "data",
        "results",
        "models",
        "config"
    ]

    for subdir in subdirs:
        subdir_path = target_dir / subdir
        subdir_path.mkdir(parents=True, exist_ok=True)
        print(f"  - Created: {subdir_path}")

    # Create the docs directory at the project root level (not under code/)
    docs_dir = project_root / "projects" / "PROJ-356-predicting-molecular-toxicity-from-struc" / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    print(f"  - Created: {docs_dir}")

    print("Directory structure creation complete.")

if __name__ == "__main__":
    main()
