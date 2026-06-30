"""
Script to initialize the project directory structure for PROJ-475.
Creates standard directories for code, data (raw/processed), specs, tests,
and configuration artifacts as defined in the implementation plan.
"""
import os
import sys

# Define the project root relative to the script location (assuming script is in root or code/)
# We will create directories relative to the current working directory to ensure
# they appear at the project root as per convention.
BASE_DIR = os.getcwd()

# Directory structure to create
# Using standard paths: code/, data/raw/, data/processed/, specs/, tests/
dirs_to_create = [
    "code",
    "code/data",
    "code/models",
    "code/utils",
    "data/raw",
    "data/processed",
    "data/schema",
    "specs",
    "tests",
    "state",
    "figures",
]

def main():
    created_count = 0
    skipped_count = 0

    print(f"Initializing project structure in: {BASE_DIR}")

    for dir_path in dirs_to_create:
        full_path = os.path.join(BASE_DIR, dir_path)
        if os.path.exists(full_path):
            # Check if it is a directory
            if os.path.isdir(full_path):
                skipped_count += 1
                print(f"  [SKIP] Directory exists: {dir_path}")
            else:
                print(f"  [ERROR] Path exists but is not a directory: {dir_path}")
                sys.exit(1)
        else:
            os.makedirs(full_path, exist_ok=True)
            created_count += 1
            print(f"  [OK] Created: {dir_path}")

    print(f"\nSetup complete. Created {created_count} new directories, skipped {skipped_count}.")
    return 0

if __name__ == "__main__":
    sys.exit(main())