"""
Script to create the project directory structure for PROJ-332.
This script creates all necessary directories as defined in task T001.
"""
import os
import sys

def main():
    # Define the root directories relative to the script location or current working directory
    # The task specifies paths relative to project root. We assume the script runs from root.
    dirs = [
        "code",
        "data/raw",
        "data/processed",
        "tests/unit",
        "tests/contract",
        "tests/integration",
        "specs/001-network-topology-thermal/contracts"
    ]

    created_count = 0
    for dir_path in dirs:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")

    print(f"Setup complete. Created {created_count} new directories.")
    return 0

if __name__ == "__main__":
    sys.exit(main())