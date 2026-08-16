import os
import sys
from pathlib import Path
from typing import List
from config import DATA_DIR, PROJECT_ROOT, LOG_DIR, ERRORS_DIR

def create_directories() -> None:
    """
    Create all required project directories.
    """
    dirs_to_create = [
        DATA_DIR,
        DATA_DIR / "raw",
        DATA_DIR / "curated",
        DATA_DIR / "artifacts",
        DATA_DIR / "logs",
        PROJECT_ROOT / "models",
        PROJECT_ROOT / "reports",
        PROJECT_ROOT / "errors",
        LOG_DIR,
        ERRORS_DIR
    ]

    for dir_path in dirs_to_create:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created/Verified directory: {dir_path}")

def create_init_files() -> None:
    """
    Create __init__.py files in all Python package directories.
    """
    python_dirs = [
        PROJECT_ROOT / "code",
        PROJECT_ROOT / "code" / "data",
        PROJECT_ROOT / "code" / "utils",
        PROJECT_ROOT / "code" / "models",
        PROJECT_ROOT / "code" / "validation",
        PROJECT_ROOT / "tests",
        PROJECT_ROOT / "tests" / "unit",
        PROJECT_ROOT / "tests" / "contract",
        PROJECT_ROOT / "tests" / "integration"
    ]

    for dir_path in python_dirs:
        init_file = dir_path / "__init__.py"
        if not init_file.exists():
            init_file.touch()
            print(f"Created __init__.py in {dir_path}")
        else:
            print(f"__init__.py already exists in {dir_path}")

def main():
    print("Setting up project data directories...")
    create_directories()
    create_init_files()
    print("Setup complete.")

if __name__ == "__main__":
    main()
