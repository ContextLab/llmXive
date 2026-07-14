"""
Script to initialize the project directory structure for PROJ-061.
Creates data/raw, data/processed, data/results, code, tests and their subdirectories.
Ensures __init__.py files exist in all Python packages.
"""
import os
from pathlib import Path

def main():
    base_dir = Path(__file__).resolve().parent.parent
    print(f"Setting up directories in: {base_dir}")

    # Define the required directory structure relative to project root
    dirs_to_create = [
        "data/raw",
        "data/processed",
        "data/results",
        "code",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "docs",
    ]

    # Create directories
    for dir_path in dirs_to_create:
        full_path = base_dir / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created: {full_path}")

    # Create __init__.py files in Python packages
    python_packages = [
        "code",
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/contract",
    ]

    for pkg_path in python_packages:
        full_path = base_dir / pkg_path
        init_file = full_path / "__init__.py"
        
        # Ensure directory exists (though it should from previous step)
        full_path.mkdir(parents=True, exist_ok=True)
        
        if not init_file.exists():
            init_file.touch()
            print(f"Created: {init_file}")
        else:
            print(f"Exists: {init_file}")

    print("Directory structure setup complete.")

if __name__ == "__main__":
    main()
