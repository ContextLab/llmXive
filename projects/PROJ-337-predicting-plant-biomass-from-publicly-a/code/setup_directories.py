"""
Script to create the project code directory structure.
Implements T001b: Create project code directories.
"""
import os
import sys
from pathlib import Path


def main():
    """
    Creates the required code directories for the project.
    Directories created:
    - code/data
    - code/models
    - code/analysis
    - code/utils
    - code/validation
    """
    # Determine the project root (assuming this script is in code/)
    # The task specifies paths relative to the project root:
    # projects/PROJ-337-.../code/{...}
    # Since we are running from code/setup_directories.py, we go up two levels
    # to reach the project root if the project root is the parent of 'code'.
    # However, the task description implies the project is at:
    # projects/PROJ-337-predicting-plant-biomass-from-publicly-a
    # and the root of the repo might be that folder or above.
    # Given T001a created `projects/.../data/...`, we assume the current working
    # directory or a known base is the project root.
    # To be robust, we assume the script is run from the project root.
    # If run from inside `code/`, we adjust.

    script_path = Path(__file__).resolve()
    current_dir = script_path.parent
    project_root = current_dir.parent  # Assuming code/ is directly under project root

    # Verify we are in the expected project structure
    # The task mentions: projects/PROJ-337-predicting-plant-biomass-from-publicly-a
    # If the current project root is NOT named that, we still create 'code' under it.
    # If the user is running from the specific project folder, this works.

    code_base = project_root / "code"
    code_base.mkdir(parents=True, exist_ok=True)

    directories = [
        "data",
        "models",
        "analysis",
        "utils",
        "validation",
    ]

    created_count = 0
    for subdir in directories:
        dir_path = code_base / subdir
        if not dir_path.exists():
            dir_path.mkdir(parents=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")

    print(f"Setup complete. Created {created_count} new directories under {code_base}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())