"""
Script to initialize the project directory structure for PROJ-543.
Creates the required folders: code/, data/raw/, data/processed/, data/results/, tests/, specs/
"""
import os
import sys

def main():
    # Define the relative paths to create from the project root
    # We assume the script is run from the project root.
    # The paths are relative to the current working directory.
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/results",
        "tests",
        "specs"
    ]

    created_count = 0
    skipped_count = 0

    for dir_path in directories:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            # Check if it is a directory, if it's a file, we might need to handle that,
            # but for this task, we assume it's either missing or a valid directory.
            if os.path.isdir(dir_path):
                print(f"Directory already exists: {dir_path}")
                skipped_count += 1
            else:
                print(f"Error: Path exists but is not a directory: {dir_path}")
                sys.exit(1)

    print(f"\nProject structure initialization complete.")
    print(f"Directories created: {created_count}")
    print(f"Directories skipped (already exist): {skipped_count}")

if __name__ == "__main__":
    main()
