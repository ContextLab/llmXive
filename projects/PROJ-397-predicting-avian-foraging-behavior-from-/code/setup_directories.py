"""
Script to initialize the project directory structure for PROJ-397.

This script creates the necessary folder hierarchy under the project root
to ensure the pipeline has a valid workspace for code, data, models, viz,
notebooks, utils, and tests.
"""
import os
import sys
from pathlib import Path

def main():
    # Define the project root relative to the script location or current working directory
    # The task specifies the root as 'projects/PROJ-397-predicting-avian-foraging-behavior-from-'
    # However, since this code lives in 'code/', we assume the script is run from the project root
    # or we construct the path relative to the script.
    # Given the task description: "Create directory structure: projects/PROJ-397.../code/{...}"
    # We will create the structure relative to the current working directory to be safe,
    # assuming the runner is in the project root.
    
    # If the script is executed from the project root:
    project_root = Path.cwd()
    
    # The task asks for the structure inside 'projects/PROJ-397-.../code/'
    # But the existing API surface shows files like 'code/setup_directories.py'.
    # This implies the 'code' directory is the root of the Python package structure.
    # We will create the subdirectories inside the 'code' directory relative to the project root.
    # To be robust, we check if we are in the project root or inside 'code'.
    
    if (project_root / "code").exists():
        base_dir = project_root / "code"
    else:
        # Fallback: assume current dir is the code dir
        base_dir = project_root

    subdirectories = [
        "data",
        "models",
        "viz",
        "notebooks",
        "utils",
        "tests"
    ]

    created_dirs = []
    
    for subdir in subdirectories:
        dir_path = base_dir / subdir
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(dir_path))
            print(f"Created directory: {dir_path}")
        except OSError as e:
            print(f"Error creating directory {dir_path}: {e}", file=sys.stderr)
            sys.exit(1)

    # Ensure __init__.py exists in Python package directories to make them importable
    # This is crucial for the imports defined in the API surface (e.g., from utils.config import ...)
    python_dirs = ["utils", "data", "models", "viz", "tests"]
    for pkg_dir in python_dirs:
        pkg_path = base_dir / pkg_dir / "__init__.py"
        if not pkg_path.exists():
            pkg_path.touch()
            print(f"Created package marker: {pkg_path}")

    print(f"Directory structure initialization complete. Created {len(created_dirs)} directories.")

if __name__ == "__main__":
    main()