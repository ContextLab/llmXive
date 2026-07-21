import os
import sys
from pathlib import Path

def create_structure():
    """
    Creates the project directory structure as per the implementation plan.
    Directories:
      - code/ (source code)
      - data/raw (raw downloaded data)
      - data/processed (processed/normalized data)
      - tests/ (unit and integration tests)
      - state/ (pipeline state and artifact hashes)
    """
    root = Path(".")
    
    dirs = [
        "code",
        "code/data",
        "code/utils",
        "code/modeling",
        "code/setup",
        "data/raw",
        "data/processed",
        "tests/unit",
        "tests/integration",
        "state",
        "results",
        "figures"
    ]

    created_count = 0
    for dir_path in dirs:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory exists: {full_path}")

    # Create placeholder __init__.py files to ensure Python package recognition
    init_files = [
        "code/__init__.py",
        "code/data/__init__.py",
        "code/utils/__init__.py",
        "code/modeling/__init__.py",
        "tests/__init__.py",
        "tests/unit/__init__.py",
        "tests/integration/__init__.py"
    ]

    for file_path in init_files:
        full_path = root / file_path
        if not full_path.exists():
            full_path.touch()
            print(f"Created placeholder: {full_path}")

    print(f"\nProject structure setup complete. {created_count} new directories created.")
    return True

if __name__ == "__main__":
    create_structure()
