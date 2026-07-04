"""
Script to initialize the project directory structure for PROJ-560.
This creates the necessary folders for source code, tests, data, and state management.
"""
import os
import sys

def create_directory(path: str) -> None:
    """Create a directory if it does not exist."""
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Created directory: {path}")
    else:
        print(f"Directory already exists: {path}")

def main() -> None:
    """Create all required project directories."""
    base_dirs = [
        "code/src",
        "code/tests",
        "data/raw",
        "data/processed",
        "data/synthetic",
        "data/derivation_logs",
        "state/projects/PROJ-560-embodied-curriculum-learning-physical-si"
    ]

    for directory in base_dirs:
        create_directory(directory)

    print("\nProject structure initialization complete.")

if __name__ == "__main__":
    main()