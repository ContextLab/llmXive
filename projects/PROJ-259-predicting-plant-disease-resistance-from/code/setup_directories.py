"""
Setup script to create the project directory tree.
Creates code/, data/, data/raw, data/processed, artifacts/, 
artifacts/models, artifacts/reports, artifacts/figures, and tests/.
"""
import os
import sys

def main():
    # Define the directory structure relative to the project root
    # The project root is assumed to be the current working directory
    directories = [
        "code",
        "data",
        "data/raw",
        "data/processed",
        "artifacts",
        "artifacts/models",
        "artifacts/reports",
        "artifacts/figures",
        "tests"
    ]

    created_count = 0
    existing_count = 0

    print("Creating project directory tree...")
    for dir_path in directories:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            print(f"  Created: {dir_path}")
            created_count += 1
        else:
            # Check if it's a file instead of a directory
            if os.path.isfile(dir_path):
                print(f"  ERROR: Path exists but is a file, not a directory: {dir_path}")
                sys.exit(1)
            else:
                print(f"  Exists: {dir_path}")
                existing_count += 1

    print(f"\nSetup complete. Created {created_count} directories, {existing_count} already existed.")

if __name__ == "__main__":
    main()