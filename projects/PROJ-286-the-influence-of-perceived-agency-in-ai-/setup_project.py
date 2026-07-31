"""
Script to initialize the project directory structure and create required __init__.py files.
This implements Task T004.
"""
import os
import sys
from pathlib import Path

def main():
    # Define the directory structure based on T004 requirements
    # Paths are relative to the project root
    directories = [
        "code/experiment",
        "code/experiment/tests",
        "code/analysis",
        "code/analysis/tests",
        "data/raw",
        "data/processed",
        "docs",
        "specs/001-perceived-agency-trust/contracts",
        "tests"
    ]

    # Create directories
    for dir_path in directories:
        full_path = Path(dir_path)
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")

    # Create __init__.py files in all code/ subdirectories and tests/ subdirectories
    init_paths = [
        "code/experiment/__init__.py",
        "code/experiment/tests/__init__.py",
        "code/analysis/__init__.py",
        "code/analysis/tests/__init__.py",
        "tests/__init__.py"
    ]

    for init_path in init_paths:
        full_path = Path(init_path)
        if not full_path.exists():
            # Write a minimal docstring to make it a proper package
            content = f'"""{full_path.parent.name} module."""\n'
            full_path.write_text(content, encoding="utf-8")
            print(f"Created file: {full_path}")
        else:
            print(f"File already exists: {full_path}")

    print("Project structure initialization complete.")

if __name__ == "__main__":
    main()