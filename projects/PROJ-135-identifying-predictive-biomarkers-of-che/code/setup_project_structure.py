import os
import sys
from pathlib import Path

def create_structure():
    """
    Creates the project directory structure as defined in plan.md and tasks.md.
    Directories created:
    - code/src/
    - code/data/raw/
    - code/data/processed/
    - code/results/
    - code/results/meta_analysis/
    - code/tests/
    - code/specs/001-chemo-biomarker-discovery/contracts/
    - code/state/
    """
    # Define the project root based on the current working directory or a standard path
    # The prompt specifies paths relative to project root, and artifacts live under code/
    # We assume the script runs from the project root.
    root = Path.cwd()
    
    # Define relative paths based on the task description
    # Note: The task description lists `src/`, but the existing API surface shows `code/src/`.
    # We will create the structure under `code/` to match the existing API surface provided.
    dirs = [
        "code/src",
        "code/data/raw",
        "code/data/processed",
        "code/results",
        "code/results/meta_analysis",
        "code/tests",
        "code/specs/001-chemo-biomarker-discovery/contracts",
        "code/state",
    ]

    created_count = 0
    for dir_path in dirs:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory exists: {full_path}")

    # Ensure __init__.py files exist in Python package directories to make them importable
    python_dirs = ["code/src", "code/tests", "code/specs/001-chemo-biomarker-discovery", "code/specs/001-chemo-biomarker-discovery/contracts"]
    for dir_path in python_dirs:
        full_path = root / dir_path / "__init__.py"
        if not full_path.exists():
            full_path.touch()
            print(f"Created empty __init__.py: {full_path}")
        else:
            print(f"__init__.py exists: {full_path}")

    if created_count == 0:
        print("No new directories were created. Structure already exists.")
    else:
        print(f"Successfully created {created_count} new directories.")

if __name__ == "__main__":
    create_structure()
