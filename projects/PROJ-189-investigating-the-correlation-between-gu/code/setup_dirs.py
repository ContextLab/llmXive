"""
Script to create the required project directory structure for PROJ-189.
This script ensures all necessary folders for data, code, tests, and docs exist.
"""
import os
from pathlib import Path

def main():
    # Define the project root based on the task description
    # The task assumes we are running from the project root or code directory
    # We will resolve relative to the script's location or current working directory
    base_path = Path.cwd()
    
    # Define the required subdirectories relative to the base path
    # Based on T001b requirements:
    # data/raw, data/processed, data/models
    # code, code/utils
    # tests, tests/contract, tests/integration, tests/unit
    # docs
    directories = [
        "data/raw",
        "data/processed",
        "data/models",
        "code",
        "code/utils",
        "tests",
        "tests/contract",
        "tests/integration",
        "tests/unit",
        "docs"
    ]

    created_count = 0
    existing_count = 0

    print(f"Creating directory structure in: {base_path}")

    for dir_path in directories:
        full_path = base_path / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created: {full_path}")
            created_count += 1
        else:
            print(f"Exists: {full_path}")
            existing_count += 1

    print(f"\nDirectory creation complete.")
    print(f"Created: {created_count} new directories.")
    print(f"Already existed: {existing_count} directories.")

if __name__ == "__main__":
    main()