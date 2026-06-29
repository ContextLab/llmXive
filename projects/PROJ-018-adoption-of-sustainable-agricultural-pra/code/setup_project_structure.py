"""
Script to initialize the project directory structure for PROJ-018.

This script creates the necessary folders for the research pipeline:
- code/
- data/raw/
- data/processed/
- results/
- tests/
- docs/

It runs idempotently (safe to run multiple times).
"""
import os
import sys

PROJECT_ROOT = "projects/PROJ-018-adoption-of-sustainable-agricultural-pra"

SUBDIRECTORIES = [
    "code",
    "data/raw",
    "data/processed",
    "results",
    "tests",
    "docs",
]

def main():
    print(f"Initializing project structure at: {PROJECT_ROOT}")
    
    created_count = 0
    skipped_count = 0

    for subdir in SUBDIRECTORIES:
        full_path = os.path.join(PROJECT_ROOT, subdir)
        if os.path.exists(full_path):
            print(f"  [SKIP] {subdir} already exists")
            skipped_count += 1
        else:
            os.makedirs(full_path, exist_ok=True)
            print(f"  [OK] Created {subdir}")
            created_count += 1

    print(f"\nSummary: {created_count} directories created, {skipped_count} skipped.")
    print("Project structure initialization complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())