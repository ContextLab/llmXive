"""
Setup script to create the project directory structure for PROJ-527.
Creates required directories for code, tests, data, and state management.
"""
import os
from pathlib import Path

def main():
    """Create the standard project directory structure."""
    # Define the root directory (current working directory)
    root = Path.cwd()

    # Define the required directories relative to root
    directories = [
        "code",
        "tests",
        "data/raw",
        "data/processed",
        "data/results",
        "state",
    ]

    created_count = 0
    for dir_path in directories:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")

    print(f"\nProject structure setup complete. Created {created_count} new directories.")
    return 0

if __name__ == "__main__":
    exit(main())