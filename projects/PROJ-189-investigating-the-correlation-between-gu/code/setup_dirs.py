"""
Script to initialize the project directory structure for PROJ-189.
Creates all required subdirectories for data, code, tests, and documentation.
"""
import os
from pathlib import Path

def main():
    # Define the project root relative to this script's location
    # The script is in code/, so root is parent of code/
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent

    # Define the required directory structure relative to project root
    dirs_to_create = [
        "data/raw",
        "data/processed",
        "data/models",
        "code",          # Already exists but ensures consistency
        "code/utils",
        "tests",
        "tests/contract",
        "tests/integration",
        "tests/unit",
        "docs",
    ]

    created_count = 0
    for dir_path in dirs_to_create:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")

    print(f"\nSetup complete. {created_count} new directories created.")
    print(f"Project root: {project_root}")

if __name__ == "__main__":
    main()
