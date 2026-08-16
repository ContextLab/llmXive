"""
Script to create the required directory structure for the project.
This script ensures that code/, data/, tests/, and docs/ subdirectories exist.
"""
import os
from pathlib import Path

def create_directory_structure():
    """Create the base directory structure if it doesn't exist."""
    base_dirs = [
        "code",
        "data",
        "tests",
        "docs"
    ]

    for dir_name in base_dirs:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
        else:
            print(f"Directory already exists: {dir_path}")

    # Create subdirectories for data
    data_subdirs = [
        "data/raw",
        "data/processed"
    ]
    for dir_name in data_subdirs:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")

    # Create subdirectories for tests
    test_subdirs = [
        "tests/contract",
        "tests/integration",
        "tests/unit"
    ]
    for dir_name in test_subdirs:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")

    # Create __init__.py files to make directories Python packages
    init_files = [
        "code/__init__.py",
        "data/__init__.py",
        "tests/__init__.py",
        "docs/__init__.py",
        "tests/contract/__init__.py",
        "tests/integration/__init__.py",
        "tests/unit/__init__.py"
    ]

    for file_path in init_files:
        path = Path(file_path)
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()
            print(f"Created init file: {file_path}")

    print("Directory structure setup complete.")

if __name__ == "__main__":
    create_directory_structure()