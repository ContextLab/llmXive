"""
Module to create the required project directory structure.
Implements Task T001b: Create subdirectories for code, data, tests, and docs.
"""
import os
import sys

def create_directories():
    """
    Creates the required directory structure for the project.
    Ensures all directories exist, creating them if necessary.
    """
    # Define the root directory (project root)
    root_dir = os.getcwd()

    # Define the required subdirectories relative to the root
    directories = [
        "code",
        "data",
        "data/raw",
        "data/processed",
        "data/visualizations",
        "tests",
        "tests/unit",
        "tests/integration",
        "docs"
    ]

    created_count = 0
    existing_count = 0

    for dir_path in directories:
        full_path = os.path.join(root_dir, dir_path)
        if not os.path.exists(full_path):
            os.makedirs(full_path)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            # Check if it is actually a directory
            if os.path.isdir(full_path):
                existing_count += 1
            else:
                # Path exists but is a file, which is an error condition
                print(f"Error: Path exists but is not a directory: {full_path}")
                sys.exit(1)

    print(f"Directory setup complete. Created: {created_count}, Existing: {existing_count}")
    return True

if __name__ == "__main__":
    create_directories()
