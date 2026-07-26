"""
Script to initialize the project directory structure as per T001.
Creates: code/, data/, tests/, docs/ and their subdirectories.
"""
import os
from pathlib import Path

def create_structure():
    root = Path(".")
    structure = [
        "code",
        "code/data",
        "code/models",
        "code/viz",
        "code/utils",
        "data",
        "data/raw",
        "data/processed",
        "data/artifacts",
        "tests",
        "tests/unit",
        "tests/integration",
        "docs",
        "specs",
        "state",
        "state/projects",
        "contracts",
    ]

    for dir_path in structure:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory exists: {full_path}")

    # Ensure __init__.py files exist for Python packages
    init_files = [
        "code/__init__.py",
        "data/__init__.py",
        "tests/__init__.py",
        "docs/__init__.py",
        "code/data/__init__.py",
        "code/models/__init__.py",
        "code/viz/__init__.py",
        "code/utils/__init__.py",
    ]

    for init_file in init_files:
        full_path = root / init_file
        if not full_path.exists():
            full_path.touch()
            print(f"Created empty init file: {full_path}")

if __name__ == "__main__":
    create_structure()
    print("Project structure initialization complete.")