"""
Directory creation script for llmXive project structure.
This script creates the necessary directory tree for code, data, results, and tests.
"""
import os
from pathlib import Path

def setup_directories():
    """
    Creates the standard project directory structure:
    - code/
    - data/raw/
    - data/processed/
    - results/plots/
    - results/reports/
    - tests/unit/
    - tests/integration/
    """
    root = Path(".")
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "results/plots",
        "results/reports",
        "tests/unit",
        "tests/integration",
    ]

    created = []
    for dir_path in directories:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created.append(str(full_path))
        else:
            # Ensure it is actually a directory
            if not full_path.is_dir():
                raise RuntimeError(f"Path {full_path} exists but is not a directory.")

    if created:
        print(f"Created directories: {', '.join(created)}")
    else:
        print("All required directories already exist.")
    
    # Create __init__.py files to make them packages where appropriate
    init_files = [
        "code/__init__.py",
        "data/__init__.py",
        "data/raw/__init__.py",
        "data/processed/__init__.py",
        "results/__init__.py",
        "results/plots/__init__.py",
        "results/reports/__init__.py",
        "tests/__init__.py",
        "tests/unit/__init__.py",
        "tests/integration/__init__.py",
    ]
    
    for init_path in init_files:
        full_init = root / init_path
        if not full_init.exists():
            full_init.touch()
            print(f"Created {init_path}")

if __name__ == "__main__":
    setup_directories()
