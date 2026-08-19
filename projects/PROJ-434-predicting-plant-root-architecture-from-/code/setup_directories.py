"""
Setup script to create the required directory structure for the project.

This script creates all necessary directories for the plant root architecture
prediction pipeline as specified in T001a.
"""

import os
from pathlib import Path


def main():
    """Create the required directory structure."""
    # Define the root directory (current working directory)
    root = Path.cwd()

    # Define all required directories
    directories = [
        "code",
        "data",
        "data/raw",
        "data/processed",
        "data/logs",
        "tests",
        "artifacts",
        "figures",
        # Subdirectories for better organization
        "code/utils",
        "code/ingestion",
        "code/modeling",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "specs/001-predict-root-architecture",
        "specs/001-predict-root-architecture/contracts",
    ]

    # Create directories
    created_count = 0
    for dir_path in directories:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")

    print(f"\nSetup complete. Created {created_count} new directories.")
    print(f"Total directories managed: {len(directories)}")


if __name__ == "__main__":
    main()
