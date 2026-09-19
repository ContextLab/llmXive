"""
Script to set up the project directory structure.
"""
import os
from pathlib import Path

def setup_directories():
    """
    Creates the necessary directory structure for the project.
    """
    # Assume this script is run from the project root or code directory
    # We determine root based on the script's location
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent if script_dir.name == "code" else script_dir

    directories = [
        "data/raw",
        "data/processed",
        "code/data",
        "code/models",
        "code/utils",
        "tests",
        "state/projects",
        "logs",
        "specs"
    ]

    for dir_path in directories:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")

    # Create __init__.py files to make directories packages
    package_dirs = ["code", "code/data", "code/models", "code/utils", "tests"]
    for pkg_dir in package_dirs:
        full_path = project_root / pkg_dir / "__init__.py"
        if not full_path.exists():
            full_path.touch()
            print(f"Created __init__.py in: {full_path}")

    print("Project directory structure setup complete.")

if __name__ == "__main__":
    setup_directories()
