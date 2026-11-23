"""
Setup script to create the required directory structure for the project.
Ensures all necessary folders for data, code, results, and tests exist.
"""
import os
import sys
from pathlib import Path

# Define the base directory (project root)
BASE_DIR = Path(__file__).resolve().parent.parent

# Define the required directory structure relative to the project root
REQUIRED_DIRS = [
    "data/raw",
    "data/processed",
    "code/models",
    "code/metrics",
    "code/stats",
    "results",
    "tests/unit",
    "tests/integration",
    "code/utils"
]

def main():
    """
    Creates all required directories if they do not already exist.
    Prints a summary of created directories.
    """
    created_count = 0
    existing_count = 0

    print(f"Project Root: {BASE_DIR}")
    print("Checking/Creating directories...")

    for dir_path in REQUIRED_DIRS:
        full_path = BASE_DIR / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created: {full_path}")
            created_count += 1
        else:
            existing_count += 1

    print("-" * 40)
    print(f"Directories created: {created_count}")
    print(f"Directories already existing: {existing_count}")
    print("Directory structure setup complete.")

    return 0

if __name__ == "__main__":
    sys.exit(main())
