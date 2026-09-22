import os
import sys
from pathlib import Path

def main():
    """
    Creates the project directory structure for PROJ-455.
    Executes the equivalent of:
    mkdir -p code/data code/models code/analysis tests/unit tests/integration tests/contract tests/benchmark contracts data/raw data/processed data/results
    """
    # Define the project root (assuming script is run from project root or parent)
    # We will create these directories relative to the current working directory
    # to ensure they appear in the project tree.
    base_path = Path.cwd()

    # Define the required directory paths relative to the base
    directories = [
        "code/data",
        "code/models",
        "code/analysis",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "tests/benchmark",
        "contracts",
        "data/raw",
        "data/processed",
        "data/results",
    ]

    created_count = 0
    skipped_count = 0

    for dir_path in directories:
        full_path = base_path / dir_path
        try:
            if not full_path.exists():
                full_path.mkdir(parents=True, exist_ok=True)
                print(f"Created directory: {full_path}")
                created_count += 1
            else:
                print(f"Directory already exists: {full_path}")
                skipped_count += 1
        except OSError as e:
            print(f"Error creating directory {full_path}: {e}", file=sys.stderr)
            return 1

    print(f"\nProject structure setup complete.")
    print(f"Created: {created_count}, Skipped (existing): {skipped_count}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
