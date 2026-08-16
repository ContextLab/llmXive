import os
import sys
from pathlib import Path

def main():
    """
    Creates the directory structure for the project.
    Specifically creates: data/raw, data/derived, code, tests, results, state
    relative to the project root.
    """
    # Define the project root based on the script location or current working directory
    # The task implies running from the project root, but we ensure paths are relative to the script's parent if needed.
    # However, standard practice for these pipelines is to run from the repo root.
    project_root = Path.cwd()
    
    # Define the specific project directory name as per task T001a
    project_name = "PROJ-150-detecting-statistical-power-drift-in-rep"
    project_path = project_root / project_name

    # Create the main project directory if it doesn't exist
    project_path.mkdir(parents=True, exist_ok=True)
    print(f"Created project directory: {project_path}")

    # Define subdirectories to create
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
        full_path = project_path / subdir
        full_path.mkdir(parents=True, exist_ok=True)
        created_dirs.append(str(full_path))
        print(f"Created directory: {full_path}")

    print(f"Directory structure for {project_name} is ready.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
