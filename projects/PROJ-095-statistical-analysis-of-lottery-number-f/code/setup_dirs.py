"""
Setup script to create project directory structure.
Implements T001a: Create project directories.
"""
import os
import sys

def main():
    """Create the required project directories."""
    # Define the relative paths to be created
    directories = [
        "data/raw",
        "data/processed",
        "data/results",
        "code",
        "tests/unit",
        "tests/integration",
        "config"
    ]

    created_count = 0
    for dir_path in directories:
        if not os.path.exists(dir_path):
          os.makedirs(dir_path)
          print(f"Created directory: {dir_path}")
          created_count += 1
        else:
          print(f"Directory already exists: {dir_path}")

    print(f"\nSetup complete. {created_count} new directories created.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
