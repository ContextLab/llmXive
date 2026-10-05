"""
Task T008: Create directory structure for the project.

Creates the following directories under the project root:
- data/raw/
- data/processed/
- data/spot_check/
- artifacts/
- tests/
"""
import os
from pathlib import Path


def main():
    """Create the required directory structure."""
    # Define the base project root (assuming script runs from project root)
    base_path = Path(".")

    # Define relative paths to create
    directories = [
        "data/raw",
        "data/processed",
        "data/spot_check",
        "artifacts",
        "tests"
    ]

    created_count = 0
    for dir_path in directories:
        full_path = base_path / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")

    print(f"Directory structure setup complete. {created_count} new directories created.")


if __name__ == "__main__":
    main()