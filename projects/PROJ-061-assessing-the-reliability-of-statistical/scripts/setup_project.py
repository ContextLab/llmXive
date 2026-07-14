"""
Script to initialize the project directory structure and create necessary __init__.py files.
This script ensures the directory layout required by T001 and T009 exists.
"""
import os
from pathlib import Path

def main():
    # Define the project root (current directory)
    root = Path(".")

    # Define the required directory structure
    # Based on T001: code/, tests/, data/raw/, data/processed/, data/results/, docs/
    # Based on T001: tests/unit/, tests/integration/, tests/contract/
    # Based on T009: data/raw/, data/processed/, data/results/, code/, tests/
    directories = [
        "code",
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "data/raw",
        "data/processed",
        "data/results",
        "docs"
    ]

    # Create directories
    for dir_path in directories:
        full_path = root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")

    # Define paths for __init__.py files
    # T001 requires __init__.py in: code/, tests/, tests/unit/, tests/integration/, tests/contract/
    init_files = [
        "code/__init__.py",
        "tests/__init__.py",
        "tests/unit/__init__.py",
        "tests/integration/__init__.py",
        "tests/contract/__init__.py"
    ]

    # Create __init__.py files
    for init_path in init_files:
        full_path = root / init_path
        if not full_path.exists():
            # Write a minimal docstring to make it a valid Python package
            full_path.write_text('"""Auto-generated init file."""\n')
            print(f"Created file: {full_path}")
        else:
            print(f"File already exists: {full_path}")

    print("\nProject structure initialization complete.")

if __name__ == "__main__":
    main()