import os
import sys
from pathlib import Path

def create_directories():
    """
    Creates the project directory structure as defined in T001a.
    Directories:
      - data/raw
      - data/processed
      - code (already exists, but ensures path)
      - tests/unit
      - tests/integration
      - tests/contract
      - specs/001-gene-regulation/contracts
    """
    # Define the project root (current working directory)
    project_root = Path.cwd()

    # Define the relative paths to be created
    directories = [
        "data/raw",
        "data/processed",
        "code",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "specs/001-gene-regulation/contracts"
    ]

    created_count = 0
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")

    return created_count

def create_init_files():
    """
    Creates empty __init__.py files in all Python package directories
    to ensure they are recognized as packages.
    """
    project_root = Path.cwd()

    # Directories that need __init__.py
    init_dirs = [
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "code" # Ensure code is treated as a package if imported relative, though usually scripts
    ]

    for dir_path in init_dirs:
        full_path = project_root / dir_path
        if full_path.exists():
            init_file = full_path / "__init__.py"
            if not init_file.exists():
                init_file.touch()
                print(f"Created __init__.py in: {full_path}")
            else:
                print(f"__init__.py already exists in: {full_path}")
        else:
            print(f"Warning: Directory not found for init file: {full_path}")

def main():
    """
    Entry point for the setup structure script.
    """
    print("Initializing project directory structure for PROJ-111...")
    dirs_created = create_directories()
    create_init_files()
    print(f"Setup complete. {dirs_created} new directories created.")

if __name__ == "__main__":
    main()
