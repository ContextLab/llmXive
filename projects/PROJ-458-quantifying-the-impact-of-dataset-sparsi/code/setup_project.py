import os
import sys
from pathlib import Path

def main():
    """
    Create the project directory structure as defined in T001.
    """
    # Define the base directory (project root)
    base_dir = Path(__file__).resolve().parent.parent

    # Define the relative paths to create
    dirs_to_create = [
        "code/utils",
        "data/raw",
        "data/processed",
        "data/results",
        "data/metadata",
        "tests/unit",
        "tests/integration",
        "docs",
    ]

    created_count = 0
    for rel_path in dirs_to_create:
        full_path = base_dir / rel_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")

    print(f"Project structure setup complete. {created_count} new directories created.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
