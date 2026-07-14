"""
Script to initialize the project directory structure as per T001.
This script ensures all required directories and __init__.py files exist.
"""
import os
import sys

def create_directories():
    """Create the required directory structure."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Define all required directories relative to the project root
    directories = [
        "code",
        "code/data",
        "code/data/raw",
        "code/data/processed",
        "code/data/results",
        "code/models",
        "code/reports",
        "code/validation",
        "code/config.py",  # Will be handled separately if needed, but directory is here
        "tests",
        "tests/contract",
        "tests/unit",
        "tests/integration",
        "data",
        "data/raw",
        "data/processed",
        "data/results",
        "specs",
        "specs/contracts"
    ]

    created_count = 0
    for dir_path in directories:
        full_path = os.path.join(base_dir, dir_path)
        if not os.path.exists(full_path):
            os.makedirs(full_path)
            created_count += 1
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")

    # Create __init__.py files in all src/ and tests/ subdirectories
    init_dirs = [
        "code",
        "code/data",
        "code/data/raw",
        "code/data/processed",
        "code/data/results",
        "code/models",
        "code/reports",
        "code/validation",
        "tests",
        "tests/contract",
        "tests/unit",
        "tests/integration"
    ]

    for dir_path in init_dirs:
        full_path = os.path.join(base_dir, dir_path)
        init_file = os.path.join(full_path, "__init__.py")
        if not os.path.exists(init_file):
            with open(init_file, "w") as f:
                f.write(f"# {dir_path.replace('/', ' ').title()} module\n")
            print(f"Created __init__.py: {init_file}")
        else:
            print(f"__init__.py already exists: {init_file}")

    print(f"\nProject structure initialization complete. Created {created_count} new directories.")

if __name__ == "__main__":
    create_directories()