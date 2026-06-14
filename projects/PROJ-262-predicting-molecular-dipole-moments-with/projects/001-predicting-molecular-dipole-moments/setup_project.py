"""
Project structure initialization script for T001.
Creates the complete directory tree per implementation plan.md.
"""
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent

# Directory structure to create
DIRECTORIES = [
    # Core directories
    "code",
    "tests",
    "data",
    "state",
    "specs",
    "results",
    # Subdirectories under code
    "code/data",
    "code/models",
    "code/training",
    "code/attribution",
    "code/analysis",
    "code/utils",
    # Subdirectories under tests
    "tests/unit",
    "tests/integration",
    "tests/contract",
    # Subdirectories under data
    "data/raw",
    "data/processed",
    "data/checkpoints",
    # Subdirectories under specs
    "specs/001-predicting-molecular-dipole-moments",
    # Subdirectories under results
    "results/figures",
]

# Placeholder files to create (ensures directories are tracked by git)
PLACEHOLDER_FILES = {
    "code/__init__.py": "",
    "code/data/__init__.py": "",
    "code/models/__init__.py": "",
    "code/training/__init__.py": "",
    "code/attribution/__init__.py": "",
    "code/analysis/__init__.py": "",
    "code/utils/__init__.py": "",
    "tests/__init__.py": "",
    "tests/unit/__init__.py": "",
    "tests/integration/__init__.py": "",
    "tests/contract/__init__.py": "",
    "data/.gitkeep": "",
    "state/.gitkeep": "",
    "results/.gitkeep": "",
}

def main():
    """Create all project directories and placeholder files."""
    created_dirs = 0
    created_files = 0

    # Create directories
    for dir_path in DIRECTORIES:
        full_path = PROJECT_ROOT / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        created_dirs += 1

    # Create placeholder files
    for file_path, content in PLACEHOLDER_FILES.items():
        full_path = PROJECT_ROOT / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)
        created_files += 1

    print(f"Created {created_dirs} directories")
    print(f"Created {created_files} placeholder files")
    print(f"Project structure initialized at {PROJECT_ROOT}")

if __name__ == "__main__":
    main()
