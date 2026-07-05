"""
Setup script to create the project directory structure.
"""
import os
import sys


def create_directories():
    """
    Create the project directory structure.
    """
    # Define the project root
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    # Define directory structure
    directories = [
        # Data directories
        "data/raw",
        "data/processed",
        "data/output",
        # Code directories
        "code/utils",
        "code/models",
        "code/tests",
        # Tests directories
        "tests/unit",
        "tests/integration",
        # Specs directories
        "specs",
        # Figures directory
        "figures",
    ]

    # Create directories
    for dir_path in directories:
        full_path = os.path.join(project_root, dir_path)
        os.makedirs(full_path, exist_ok=True)
        print(f"Created directory: {full_path}")

    print("Project directory structure created successfully.")


if __name__ == "__main__":
    create_directories()