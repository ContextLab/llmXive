"""
Script to initialize the project directory structure.
Creates the required directories for code, data, tests, and specs.
"""
import os
import sys
import logging
from pathlib import Path

# Ensure the project root is in the path if running as a script
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
os.chdir(PROJECT_ROOT)

REQUIRED_DIRS = [
    "code",
    "code/cli",
    "code/data",
    "code/data/raw",
    "code/data/processed",
    "code/data/interim",
    "code/modeling",
    "code/models",
    "code/utils",
    "code/scripts",
    "code/tests",
    "code/tests/unit",
    "code/tests/integration",
    "data",
    "data/raw",
    "data/processed",
    "data/interim",
    "figures",
    "tests",
    "tests/unit",
    "tests/integration",
    "specs",
    "state",
    "state/projects",
]

def main():
    """Create the project directory structure."""
    print(f"Initializing project structure in: {PROJECT_ROOT}")
    created_count = 0

    for dir_path in REQUIRED_DIRS:
        full_path = PROJECT_ROOT / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory exists: {dir_path}")

    # Create placeholder __init__.py files for Python packages
    init_files = [
        "code/__init__.py",
        "code/cli/__init__.py",
        "code/data/__init__.py",
        "code/modeling/__init__.py",
        "code/models/__init__.py",
        "code/utils/__init__.py",
        "code/scripts/__init__.py",
        "code/tests/__init__.py",
        "code/tests/unit/__init__.py",
        "code/tests/integration/__init__.py",
        "tests/__init__.py",
        "tests/unit/__init__.py",
        "tests/integration/__init__.py",
    ]

    for init_file in init_files:
        full_path = PROJECT_ROOT / init_file
        if not full_path.exists():
            full_path.write_text("")
            print(f"Created init file: {init_file}")

    print(f"\nProject structure initialization complete. Created {created_count} new directories.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
