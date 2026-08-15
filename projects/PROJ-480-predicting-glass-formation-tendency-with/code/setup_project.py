"""
Setup script to create the project directory structure for llmXive PROJ-480.

This script implements Task T001 by creating all required directories
relative to the project root.
"""
import os
import sys
from pathlib import Path


def main():
    # Define the base directory (project root)
    # We assume the script is run from the project root or the code directory
    # We will resolve relative to the current working directory to be safe
    base_path = Path.cwd()

    # Define all required directories relative to the project root
    # Based on T001 description:
    # src/data, src/models, src/reports, src/cli, src/lib
    # tests/contract, tests/unit, tests/integration
    # data/raw, data/processed
    # state/
    # reports/
    
    directories = [
        "src/data",
        "src/models",
        "src/reports",
        "src/cli",
        "src/lib",
        "tests/contract",
        "tests/unit",
        "tests/integration",
        "data/raw",
        "data/processed",
        "state",
        "reports",
    ]

    created_count = 0
    skipped_count = 0

    print(f"Creating project structure in: {base_path}")

    for dir_path in directories:
        full_path = base_path / dir_path
        try:
            if not full_path.exists():
                full_path.mkdir(parents=True, exist_ok=True)
                print(f"Created: {dir_path}")
                created_count += 1
            else:
                print(f"Exists:  {dir_path}")
                skipped_count += 1
        except OSError as e:
            print(f"Error creating {dir_path}: {e}")
            sys.exit(1)

    print(f"\nSetup complete. Created: {created_count}, Skipped: {skipped_count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
