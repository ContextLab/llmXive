import os
import sys
from pathlib import Path

def create_directory_structure():
    """Create the project directory structure as specified in T004."""
    base_dirs = [
        "code/experiment",
        "code/experiment/tests",
        "code/analysis",
        "code/analysis/tests",
        "data/raw",
        "data/processed",
        "docs",
        "specs/001-perceived-agency-trust/contracts"
    ]

    for dir_path in base_dirs:
        full_path = Path(dir_path)
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")

def create_init_files():
    """Create __init__.py files in all code/ and tests/ subdirectories."""
    init_paths = [
        "code/experiment/__init__.py",
        "code/experiment/tests/__init__.py",
        "code/analysis/__init__.py",
        "code/analysis/tests/__init__.py"
    ]

    for init_path in init_paths:
        full_path = Path(init_path)
        # Create the file if it doesn't exist, or leave it empty if it does
        if not full_path.exists():
            full_path.touch()
            print(f"Created file: {full_path}")
        else:
            print(f"File already exists (skipped): {full_path}")

def main():
    """Main entry point to execute the structure setup."""
    create_directory_structure()
    create_init_files()
    print("Project structure setup complete.")

if __name__ == "__main__":
    main()
