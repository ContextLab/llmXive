"""
Script to initialize the project directory structure.
This ensures all required folders exist before data processing begins.
"""
import os
from pathlib import Path

def main():
    root = Path(__file__).resolve().parent.parent
    print(f"Initializing project structure at: {root}")

    directories = [
        "code",
        "data/raw",
        "data/processed",
        "results/associations",
        "results/plots",
        "results/power",
        "results/sensitivity",
        "results/validation",
        "tests",
    ]

    for dir_path in directories:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")

    # Ensure __init__.py files exist for Python packages
    init_files = [
        root / "code" / "__init__.py",
        root / "data" / "__init__.py",
        root / "data" / "raw" / "__init__.py",
        root / "data" / "processed" / "__init__.py",
        root / "results" / "__init__.py",
        root / "results" / "associations" / "__init__.py",
        root / "results" / "plots" / "__init__.py",
        root / "results" / "power" / "__init__.py",
        root / "results" / "sensitivity" / "__init__.py",
        root / "results" / "validation" / "__init__.py",
        root / "tests" / "__init__.py",
    ]

    for init_file in init_files:
        if not init_file.exists():
            init_file.touch()
            print(f"Created __init__.py: {init_file}")
        else:
            print(f"__init__.py already exists: {init_file}")

    print("Project structure initialization complete.")

if __name__ == "__main__":
    main()