"""
Setup script to create the project directory structure.
Implements Task T001a.
"""
import os
import sys

def main():
    """
    Creates the required project directories:
    data/raw, data/processed, data/results, code, tests/unit, tests/integration, config
    """
    # Define the relative paths to create
    directories = [
        "data/raw",
        "data/processed",
        "data/results",
        "code",
        "tests/unit",
        "tests/integration",
        "config"
    ]

    # Get the project root (assuming this script is in code/)
    # We need to go up one level to the root to create directories there
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)

    created_count = 0
    for dir_name in directories:
        full_path = os.path.join(project_root, dir_name)
        if not os.path.exists(full_path):
            os.makedirs(full_path)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")

    print(f"Setup complete. {created_count} new directories created.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
