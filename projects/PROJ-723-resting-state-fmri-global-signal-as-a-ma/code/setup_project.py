"""
Project Initialization Script for llmXive PROJ-723.

This script creates the necessary directory structure and initializes
the Python project configuration files required for the pipeline.

It ensures that `code/`, `data/raw/`, `data/processed/`, and `tests/`
directories exist at the repository root.

Usage:
    python code/setup_project.py
"""
import os
import sys
from pathlib import Path

# Define the project root (parent of the 'code' directory)
# Assuming this script is run from the repository root or code/
def get_project_root():
    current_path = Path(__file__).resolve()
    # If running from code/setup_project.py, root is parent
    if current_path.parent.name == "code":
        return current_path.parent.parent
    return current_path.parent

def create_directory(path: Path, description: str):
    """Create a directory if it doesn't exist and log the action."""
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        print(f"[OK] Created directory: {path} ({description})")
    else:
        if path.is_dir():
            print(f"[SKIP] Directory exists: {path}")
        else:
            raise RuntimeError(f"[ERROR] Path exists but is not a directory: {path}")

def main():
    root = get_project_root()
    print(f"Project root identified at: {root}")

    # Define required directories based on T001a-d requirements
    dirs_to_create = [
        (root / "code", "Source code"),
        (root / "data" / "raw", "Raw data storage"),
        (root / "data" / "processed", "Processed data storage"),
        (root / "tests", "Unit and integration tests"),
    ]

    errors = []
    for path, desc in dirs_to_create:
        try:
            create_directory(path, desc)
        except Exception as e:
            errors.append(str(e))

    if errors:
        print("\n[FAILED] Project initialization encountered errors:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)

    print("\n[SUCCESS] Project structure initialized successfully.")
    print("Next steps: Install dependencies via 'pip install -r requirements.txt'")

if __name__ == "__main__":
    main()
