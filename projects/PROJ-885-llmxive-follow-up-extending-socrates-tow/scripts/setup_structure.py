"""
Script to initialize the project directory structure for llmXive.
This script creates the required directories as defined in plan.md.
"""
import os
from pathlib import Path

def main():
    root = Path(".")
    structure = [
        "code",
        "data/raw",
        "data/processed",
        "data/results",
        "tests",
        "contracts"
    ]

    created_count = 0
    for dir_path in structure:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory exists: {full_path}")

    # Ensure __init__.py files exist for Python packages
    init_files = [
        "code/__init__.py",
        "data/raw/__init__.py",
        "data/processed/__init__.py",
        "data/results/__init__.py",
        "tests/__init__.py",
        "contracts/__init__.py"
    ]

    for init_file in init_files:
        full_path = root / init_file
        if not full_path.exists():
            full_path.write_text(f"# {init_file}\n")
            print(f"Created init file: {full_path}")
            created_count += 1
        else:
            print(f"Init file exists: {full_path}")

    print(f"\nSetup complete. Created/verified {created_count} items.")

if __name__ == "__main__":
    main()