"""
Project Structure Initialization Script.

This script creates the required directory structure and initializes
__init__.py files for the llmXive automated science pipeline.
"""
import os
import sys
from pathlib import Path


def create_project_structure():
    """
    Create directories and __init__.py files as per implementation plan.

    Required structure:
    - code/
    - data/raw/
    - data/processed/
    - results/
    - specs/
    - tests/
    - tests/unit/
    - tests/integration/
    """
    # Define the base directory (project root)
    base_dir = Path(__file__).resolve().parent.parent

    # Define the directory structure relative to the project root
    # Note: 'code' is the root for source files in this project structure
    # so we create it relative to the script's location if needed,
    # but typically scripts run from root. We assume script is in code/
    # and we need to create structure relative to the repo root.
    # Since the script is at code/setup_project.py, parent is project root.
    root = base_dir

    directories = [
        "code",
        "data/raw",
        "data/processed",
        "results",
        "specs",
        "tests",
        "tests/unit",
        "tests/integration",
    ]

    created_dirs = []
    created_files = []

    for dir_path in directories:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(full_path.relative_to(root)))

        # Create __init__.py if this is a Python package directory
        # We initialize __init__.py in all directories to ensure they are treated as packages
        # and to satisfy the verification requirement.
        init_file = full_path / "__init__.py"
        if not init_file.exists():
            # Create an empty __init__.py or with a docstring
            init_file.write_text("# Auto-generated package initialization\n")
            created_files.append(str(init_file.relative_to(root)))

    return created_dirs, created_files


if __name__ == "__main__":
    print("Initializing project structure...")
    created_dirs, created_files = create_project_structure()
    print(f"Created directories: {created_dirs}")
    print(f"Created __init__.py files: {created_files}")
    print("Project structure initialization complete.")
