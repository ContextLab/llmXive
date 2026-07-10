"""
Script to verify the project directory structure exists as required by T001a.
Run this script to ensure the skeleton is correctly initialized.
"""
import os
import sys

REQUIRED_DIRS = [
    "code",
    "code/ingestion",
    "code/analysis",
    "code/stats",
    "code/utils",
    "code/models",
    "data",
    "data/raw",
    "data/processed",
    "tests",
    "tests/unit",
    "tests/integration",
    "tests/contract",
    "state"
]

def main():
    base = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(base)
    missing = []

    for rel_dir in REQUIRED_DIRS:
        full_path = os.path.join(project_root, rel_dir)
        if not os.path.isdir(full_path):
            missing.append(rel_dir)

    if missing:
        print("ERROR: The following directories are missing:")
        for d in missing:
            print(f"  - {d}")
        sys.exit(1)
    else:
        print("SUCCESS: All required project directories exist.")
        return 0

if __name__ == "__main__":
    sys.exit(main())