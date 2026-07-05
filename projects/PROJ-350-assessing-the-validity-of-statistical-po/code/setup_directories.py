"""
Script to initialize the project directory structure for PROJ-350.
Creates the required folders as per tasks.md T001a.
"""
import os
import sys

def main():
    # Define the relative paths to create from the project root
    # Based on tasks.md T001a: code/, data/raw/, data/derived/, tests/, specs/, results/, docs/
    paths_to_create = [
        "code",
        "data/raw",
        "data/derived",
        "tests",
        "specs",
        "results",
        "docs"
    ]

    created_count = 0
    skipped_count = 0

    for path in paths_to_create:
        try:
            if not os.path.exists(path):
                os.makedirs(path, exist_ok=True)
                print(f"Created directory: {path}")
                created_count += 1
            else:
                print(f"Directory already exists: {path}")
                skipped_count += 1
        except PermissionError as e:
            print(f"Error: Permission denied creating {path}: {e}", file=sys.stderr)
            sys.exit(1)
        except OSError as e:
            print(f"Error: OS error creating {path}: {e}", file=sys.stderr)
            sys.exit(1)

    print(f"\nDirectory initialization complete. Created: {created_count}, Skipped: {skipped_count}")

if __name__ == "__main__":
    main()