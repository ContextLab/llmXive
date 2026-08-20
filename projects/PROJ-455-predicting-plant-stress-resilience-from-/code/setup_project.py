"""
Project Structure Initialization Script.

This script creates the directory structure required for the llmXive
automated science pipeline project PROJ-455.
"""
import os
import sys
from pathlib import Path


def main():
    """Create the project directory structure."""
    # Define the base directory relative to the script location or current working dir
    # The task specifies creating these under the project root.
    # We assume the script is run from the project root or code/ directory.
    # To be safe, we create them relative to the current working directory.
    base_path = Path.cwd()

    # Define the required directories
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
    existing_count = 0

    print(f"Initializing project structure in: {base_path}")

    for dir_path in directories:
        full_path = base_path / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created: {full_path}")
            created_count += 1
        else:
            existing_count += 1
            # Optionally print existing to verify, but keep output clean
            # print(f"Exists: {full_path}")

    print(f"Project structure initialization complete.")
    print(f"  New directories created: {created_count}")
    print(f"  Directories already existing: {existing_count}")

    return 0


if __name__ == "__main__":
    sys.exit(main())