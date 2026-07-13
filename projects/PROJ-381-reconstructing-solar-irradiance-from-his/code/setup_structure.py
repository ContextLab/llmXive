"""
Script to initialize the project directory structure for the solar irradiance reconstruction project.
This script creates the necessary directories and placeholder files to ensure the project is ready for development.
"""
import os
from pathlib import Path

def create_structure():
    """Create the required project directory structure."""
    # Define the root directories
    root_dirs = [
        "code",
        "tests",
        "data/raw",
        "data/processed",
        "code/models",
        "code/analysis"
    ]

    # Create directories
    for dir_path in root_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")

    # Create __init__.py files in code/ subdirectories and tests/
    init_dirs = [
        "code",
        "code/data",
        "code/models",
        "code/analysis",
        "tests"
    ]

    for dir_path in init_dirs:
        init_file = Path(dir_path) / "__init__.py"
        init_file.touch(exist_ok=True)
        print(f"Created __init__.py in: {dir_path}")

    # Create .gitkeep files in data directories
    gitkeep_dirs = [
        "data/raw",
        "data/processed"
    ]

    for dir_path in gitkeep_dirs:
        gitkeep_file = Path(dir_path) / ".gitkeep"
        gitkeep_file.touch(exist_ok=True)
        print(f"Created .gitkeep in: {dir_path}")

    print("\nProject structure initialization complete.")

if __name__ == "__main__":
    create_structure()
