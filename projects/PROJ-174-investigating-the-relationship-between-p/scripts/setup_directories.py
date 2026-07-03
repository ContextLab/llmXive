#!/usr/bin/env python3
"""
Script to initialize the project directory structure as defined in tasks.md (T001a).
Creates: code/, tests/, data/raw/, data/processed/, results/, state/
"""
import os
import sys

DIRECTORIES = [
    "code",
    "tests",
    "data/raw",
    "data/processed",
    "results",
    "state",
]

def main():
    root = os.getcwd()
    created_count = 0
    existing_count = 0

    for dir_path in DIRECTORIES:
        full_path = os.path.join(root, dir_path)
        if os.path.exists(full_path):
            existing_count += 1
            print(f"Directory exists: {full_path}")
        else:
            os.makedirs(full_path, exist_ok=True)
            created_count += 1
            print(f"Created directory: {full_path}")

    print(f"\nSetup complete. Created: {created_count}, Existing: {existing_count}")
    return 0

if __name__ == "__main__":
    sys.exit(main())