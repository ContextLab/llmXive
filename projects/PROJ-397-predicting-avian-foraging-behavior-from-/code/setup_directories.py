import os
import sys
from pathlib import Path

def main():
    """
    Initialize the project directory structure for PROJ-397.
    Creates the required subdirectories under projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/
    """
    # Define the base project path relative to the repository root
    # The prompt specifies the project is at: projects/PROJ-397-predicting-avian-foraging-behavior-from-/
    project_root = Path(__file__).parent.parent
    base_path = project_root / "projects" / "PROJ-397-predicting-avian-foraging-behavior-from-" / "code"

    # Define the required subdirectories
    subdirs = [
        "data",
        "models",
        "viz",
        "notebooks",
        "utils",
        "tests"
    ]

    # Create the base directory if it doesn't exist
    base_path.mkdir(parents=True, exist_ok=True)
    print(f"Base directory created/verified: {base_path}")

    # Create each subdirectory
    created_dirs = []
    for subdir in subdirs:
        dir_path = base_path / subdir
        dir_path.mkdir(parents=True, exist_ok=True)
        created_dirs.append(dir_path)
        print(f"Directory created: {dir_path}")

    # Create __init__.py files in each directory to make them Python packages
    for subdir in subdirs:
        init_path = base_path / subdir / "__init__.py"
        init_path.touch(exist_ok=True)
        print(f"Initialized package: {init_path}")

    # Create __init__.py in the root code directory as well
    root_init = base_path / "__init__.py"
    root_init.touch(exist_ok=True)

    print(f"Project structure initialization complete for {base_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
