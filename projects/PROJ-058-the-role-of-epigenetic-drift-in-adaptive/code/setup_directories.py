"""
Setup script to create the required directory structure for the project.
This script ensures that all necessary directories for output, tests, logs,
and processed data exist before the pipeline runs.
"""
import os
import sys
from pathlib import Path

def create_directories():
    """Create all required directories for the project."""
    base_dir = Path(__file__).resolve().parent.parent

    # Define all required directories
    directories = [
        base_dir / "output",
        base_dir / "output" / "figures",
        base_dir / "tests",
        base_dir / "tests" / "unit",
        base_dir / "tests" / "contract",
        base_dir / "logs",
        base_dir / "data" / "processed",
    ]

    created_count = 0
    for dir_path in directories:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")

    print(f"\nTotal directories created: {created_count}")
    print("Directory structure setup complete.")

def main():
    """Entry point for the script."""
    try:
        create_directories()
        return 0
    except Exception as e:
        print(f"Error during directory creation: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
