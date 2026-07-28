import os
import sys
from pathlib import Path

def create_directories():
    """
    Create the project directory structure as defined in the implementation plan.
    This script ensures all necessary folders exist for data, models, analysis,
    tests, and documentation.
    """
    # Define the project root (assuming this script is in code/)
    # We need to go up one level to get to the root where 'src' and 'data' live
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent

    # Define relative paths to create
    directories = [
        "src/data",
        "src/models",
        "src/analysis",
        "data/raw",
        "data/processed",
        "data/interim",
        "tests/contract",
        "tests/unit",
        "tests/integration",
        "docs"
    ]

    created_count = 0
    for dir_name in directories:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")

    print(f"\nSetup complete. {created_count} new directories created.")
    return created_count

if __name__ == "__main__":
    create_directories()