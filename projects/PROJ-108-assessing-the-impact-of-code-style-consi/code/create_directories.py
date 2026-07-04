"""
Script to create the required project directory structure for the llmXive pipeline.
Creates code/, data/, tests/ and their subdirectories at the repository root.
"""
import os
from pathlib import Path

def main():
    # Define the root directory (current working directory)
    root = Path.cwd()

    # Define the required directory structure relative to root
    directories = [
        "code",
        "data",
        "tests",
        "data/raw",
        "data/processed",
        "data/metadata",
        "tests/unit",
        "tests/integration",
    ]

    created_count = 0
    existing_count = 0

    for dir_path in directories:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            if full_path.is_dir():
                print(f"Directory already exists: {full_path}")
                existing_count += 1
            else:
                raise RuntimeError(f"Path exists but is not a directory: {full_path}")

    print(f"\nDirectory setup complete. Created: {created_count}, Existing: {existing_count}")

if __name__ == "__main__":
    main()
