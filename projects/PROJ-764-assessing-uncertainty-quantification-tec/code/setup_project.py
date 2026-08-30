"""
Setup script to create the project directory structure.
This script creates the required directories for the llmXive pipeline:
code/, data/, results/, tests/, docs/
"""
import os
from pathlib import Path

def main():
    """Create the project directory structure."""
    # Define the directories to create relative to the project root
    directories = [
        "code",
        "data",
        "results",
        "tests",
        "docs"
    ]

    # Create each directory if it doesn't exist
    for dir_name in directories:
        dir_path = Path(dir_name)
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")

    # Create subdirectories for better organization
    subdirectories = [
        "data/raw",
        "data/processed",
        "results/models",
        "results/models/ensemble_models",
        "logs",
        "tests/unit",
        "tests/contract",
        "tests/integration",
        "specs",
        "contracts"
    ]

    for subdir in subdirectories:
        subdir_path = Path(subdir)
        subdir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created subdirectory: {subdir_path}")

    print("Project directory structure created successfully.")

if __name__ == "__main__":
    main()