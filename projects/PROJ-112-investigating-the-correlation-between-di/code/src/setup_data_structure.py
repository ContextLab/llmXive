"""
Script to initialize the project directory structure as per the implementation plan.
Creates necessary folders for data, code, tests, and documentation.
"""
import os
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

def get_project_root():
    """Returns the root directory of the project."""
    return project_root

def setup_directories():
    """
    Creates the required directory structure for the project.
    """
    root = get_project_root()
    
    directories = [
        "src",
        "src/ingestion",
        "src/preprocessing",
        "src/analysis",
        "src/utils",
        "tests",
        "tests/contract",
        "tests/integration",
        "tests/unit",
        "data/raw",
        "data/processed",
        "data/processed/results",
        "docs",
        "state"
    ]

    created = []
    for dir_name in directories:
        dir_path = root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created.append(dir_name)
            print(f"Created directory: {dir_path}")
        else:
            print(f"Directory already exists: {dir_path}")

    if not created:
        print("No new directories created. Structure is already in place.")
    else:
        print(f"Successfully created {len(created)} directories.")
    
    return created

def main():
    """Entry point for the setup script."""
    print(f"Project root: {get_project_root()}")
    setup_directories()
    return 0

if __name__ == "__main__":
    sys.exit(main())
