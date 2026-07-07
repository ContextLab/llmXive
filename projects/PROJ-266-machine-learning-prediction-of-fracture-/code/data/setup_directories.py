"""
T001b: Create data directories for the fracture toughness prediction project.

This script initializes the required directory structure under `data/` to support
the ingestion, processing, and explainability workflows.

Directories created:
  - data/
  - data/raw/
  - data/processed/
  - data/explainability/
"""

import os
import sys

# Define the project root relative to this script's location
# Assuming this script is at code/data/setup_directories.py
# The project root is two levels up
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_ROOT = os.path.join(PROJECT_ROOT, "data")

REQUIRED_DIRS = [
    "data",
    "data/raw",
    "data/processed",
    "data/explainability",
]

def main():
    """Create the required directory structure if it doesn't exist."""
    created_count = 0
    skipped_count = 0

    print(f"Initializing data directories at: {DATA_ROOT}")

    for dir_path in REQUIRED_DIRS:
        full_path = os.path.join(PROJECT_ROOT, dir_path)
        if not os.path.exists(full_path):
            os.makedirs(full_path, exist_ok=True)
            print(f"[CREATED] {full_path}")
            created_count += 1
        else:
            print(f"[EXISTS] {full_path}")
            skipped_count += 1

    print(f"\nDirectory setup complete. Created: {created_count}, Skipped: {skipped_count}")
    return 0

if __name__ == "__main__":
    sys.exit(main())