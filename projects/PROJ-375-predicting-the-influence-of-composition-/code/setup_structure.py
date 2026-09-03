import os
import sys
from pathlib import Path

def create_directories():
    """
    Create the standard project directory structure.
    This function ensures that all necessary directories for code, data, tests,
    and documentation exist in the repository root.
    """
    # Define the directory structure relative to the project root
    # Assuming this script is run from the repository root or code/
    # We use a relative path that works if run from root or code/
    
    # Base directories
    dirs = [
        "code/ingestion",
        "code/features",
        "code/modeling",
        "code/utils",
        "data/raw",
        "data/processed",
        "tests/unit",
        "tests/integration",
        "docs",
        "results",
        "contracts",
        "logs",
        "code/models"  # Specifically for T001b
    ]

    # Determine the base path. If run as a script, assume current working dir is root.
    # If imported, we might need to adjust, but typically this is run via CLI.
    base_path = Path(".")

    for dir_path in dirs:
        full_path = base_path / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")

if __name__ == "__main__":
    create_directories()