import os
import sys
from pathlib import Path

def main():
    """
    Create the project directory structure as defined in the implementation plan.
    Directories created:
    - code/data
    - code/analysis
    - code/tests
    - data/raw
    - data/processed
    - docs/output
    """
    # Define the project root (assuming code/setup_project.py is at code/setup_project.py)
    # We need to go up one level to reach the project root
    project_root = Path(__file__).resolve().parent.parent

    directories = [
        project_root / "code" / "data",
        project_root / "code" / "analysis",
        project_root / "code" / "tests",
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "docs" / "output",
    ]

    created_count = 0
    for dir_path in directories:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")

    print(f"Project structure setup complete. {created_count} new directories created.")

if __name__ == "__main__":
    main()
