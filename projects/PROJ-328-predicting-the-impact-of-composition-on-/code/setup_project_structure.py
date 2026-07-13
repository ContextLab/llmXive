"""
Project Structure Setup Script for PROJ-328.

Creates the required directory hierarchy:
- projects/PROJ-328-predicting-the-impact-of-composition-on-/data/
- projects/PROJ-328-predicting-the-impact-of-composition-on-/code/
- projects/PROJ-328-predicting-the-impact-of-composition-on-/tests/
- projects/PROJ-328-predicting-the-impact-of-composition-on-/models/

Also creates necessary subdirectories for data organization.
"""
import os
import sys
from pathlib import Path


def main():
    """Create the project directory structure."""
    # Define the project root based on the task description
    project_root_name = "PROJ-328-predicting-the-impact-of-composition-on-"
    project_root = Path("projects") / project_root_name

    # Define required directories
    directories = [
        project_root,
        project_root / "data",
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "outputs",
        project_root / "data" / "checksums",
        project_root / "code",
        project_root / "tests",
        project_root / "tests" / "contract",
        project_root / "tests" / "integration",
        project_root / "tests" / "unit",
        project_root / "models",
        project_root / "specs",
    ]

    created_count = 0
    existing_count = 0

    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {directory}")
        else:
            existing_count += 1
            print(f"Directory already exists: {directory}")

    # Create .gitkeep files to ensure directories are tracked by git
    for directory in directories:
        gitkeep = directory / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()
            print(f"Created .gitkeep in: {directory}")

    print(f"\nProject structure setup complete.")
    print(f"Created {created_count} new directories.")
    print(f"Found {existing_count} existing directories.")
    print(f"Project root: {project_root.absolute()}")

    return 0


if __name__ == "__main__":
    sys.exit(main())