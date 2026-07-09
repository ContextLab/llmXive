"""
Setup script for PROJ-113: The Effect of Anticipated Regret on Choice Deferral.

Task T004: Create data directories and schema for raw/processed files.

This script initializes the required directory structure for the project's
data pipeline, ensuring that `data/raw/` and `data/processed/` exist
before ingestion and processing steps begin.
"""

import os
import sys

# Define the project root relative to this script's location
# Assuming script is at code/setup_directories.py, root is parent of code/
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# Define required directories relative to project root
REQUIRED_DIRS = [
    "data/raw",
    "data/processed",
    "data/results",
    "figures",
]

def ensure_directories():
    """
    Creates the necessary directory structure for the project.
    Prints status for each directory and exits with error if creation fails.
    """
    created_count = 0
    skipped_count = 0
    error_count = 0

    print(f"Project Root: {PROJECT_ROOT}")
    print("-" * 40)

    for dir_path in REQUIRED_DIRS:
        full_path = os.path.join(PROJECT_ROOT, dir_path)
        try:
            if os.path.exists(full_path):
                print(f"[SKIP] Exists: {dir_path}")
                skipped_count += 1
            else:
                os.makedirs(full_path, exist_ok=True)
                print(f"[CREATE] Created: {dir_path}")
                created_count += 1
        except OSError as e:
            print(f"[ERROR] Failed to create {dir_path}: {e}")
            error_count += 1

    print("-" * 40)
    print(f"Summary: {created_count} created, {skipped_count} skipped, {error_count} errors")

    if error_count > 0:
        print("FATAL: Directory creation failed. Aborting.")
        sys.exit(1)
    else:
        print("SUCCESS: Directory structure verified.")
        sys.exit(0)

if __name__ == "__main__":
    ensure_directories()