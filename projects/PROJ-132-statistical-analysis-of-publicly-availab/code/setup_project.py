"""
Project setup module for creating the directory structure
for the statistical analysis of bird migration patterns.
"""
import os
import sys
from pathlib import Path


def create_directories():
    """
    Create the project directory structure as defined in the implementation plan.

    Creates the following directories relative to the project root:
    - src/data, src/models, src/analysis
    - data/raw, data/processed, data/interim
    - tests/contract, tests/unit, tests/integration
    - docs
    """
    # Define the directory structure relative to project root
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
        "docs",
    ]

    # Get the project root (assuming this script is in code/ directory)
    # We need to go up one level to reach the project root
    current_path = Path(__file__).resolve()
    project_root = current_path.parent

    # Create each directory
    created_count = 0
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path.relative_to(project_root)}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path.relative_to(project_root)}")

    print(f"\nSetup complete. Created {created_count} new directories.")
    return True


if __name__ == "__main__":
    success = create_directories()
    sys.exit(0 if success else 1)