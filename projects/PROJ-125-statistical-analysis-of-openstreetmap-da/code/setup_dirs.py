"""
Setup script to create the project directory structure.
This script creates all necessary directories for the project.
"""
import os
import sys
from pathlib import Path

def main():
    """Create the project directory structure."""
    # Define the base directory (project root)
    base_dir = Path(__file__).resolve().parent.parent

    # Define all required directories
    directories = [
        "code",
        "data",
        "tests",
        "docs",
        "data/raw",
        "data/processed",
        "data/results",
    ]

    # Create directories
    created_count = 0
    for dir_path in directories:
        full_path = base_dir / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")

    print(f"\nSetup complete. Created {created_count} new directories.")
    return 0

if __name__ == "__main__":
    sys.exit(main())