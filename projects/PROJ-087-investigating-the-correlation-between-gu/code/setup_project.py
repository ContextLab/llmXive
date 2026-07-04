"""
Setup script for PROJ-087-investigating-the-correlation-between-gu.
Creates the required directory structure and initializes __init__.py files.
"""
import os
from pathlib import Path

def main():
    # Define the project root relative to where this script is run
    # Assuming this script is run from the project root
    project_root = Path(".")

    # Define the directories to create
    directories = [
        "src",
        "data/raw",
        "data/processed",
        "tests/unit",
        "tests/integration",
        "docs",
    ]

    # Define the paths for __init__.py files
    init_files = [
        "src/__init__.py",
        "tests/__init__.py",
        "tests/unit/__init__.py",
        "tests/integration/__init__.py",
    ]

    # Create directories
    for dir_path in directories:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")

    # Create __init__.py files
    for init_path in init_files:
        full_path = project_root / init_path
        full_path.touch(exist_ok=True)
        print(f"Created file: {full_path}")

    print("Project structure setup complete.")

if __name__ == "__main__":
    main()
