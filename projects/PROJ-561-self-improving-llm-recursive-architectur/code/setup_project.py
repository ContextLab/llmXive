import os
import sys
from pathlib import Path

def create_project_structure():
    """
    Creates the required project directory structure and __init__.py files.
    Directories created:
      - code/
      - data/raw/
      - data/processed/
      - results/
      - specs/
      - tests/
      - tests/unit/
      - tests/integration/
    """
    base_dir = Path(__file__).resolve().parent.parent
    root_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "results",
        "specs",
        "tests",
        "tests/unit",
        "tests/integration"
    ]

    created_dirs = []
    for dir_path in root_dirs:
        full_path = base_dir / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        created_dirs.append(str(full_path))

    # Create __init__.py files in Python package directories
    init_dirs = [
        "code",
        "tests",
        "tests/unit",
        "tests/integration"
    ]

    for dir_path in init_dirs:
        full_path = base_dir / dir_path / "__init__.py"
        # Create empty __init__.py if it doesn't exist
        if not full_path.exists():
            full_path.touch()
            print(f"Created: {full_path}")

    print(f"Project structure created successfully at: {base_dir}")
    print("Directories created:")
    for d in created_dirs:
        print(f"  - {d}")
    
    return created_dirs

if __name__ == "__main__":
    create_project_structure()
