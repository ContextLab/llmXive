"""
Setup script for creating project directory structure.
Creates required directories for code, data, results, and plots.
"""
import os
import sys
from typing import List

# Define the directory structure relative to project root
REQUIRED_DIRS: List[str] = [
    "code",
    "data",
    "data/raw",
    "data/processed",
    "results",
    "results/plots",
    "tests",
    "tests/unit",
    "tests/integration",
    "specs",
    "figures"
]

def ensure_directories() -> None:
    """
    Create all required directories if they do not already exist.
    Prints status to stdout for verification.
    """
    created_count = 0
    for dir_path in REQUIRED_DIRS:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")
    
    print(f"\nDirectory setup complete. Created {created_count} new directories.")

def main() -> None:
    """Entry point for the setup script."""
    print("Starting directory initialization...")
    ensure_directories()
    print("Initialization finished.")

if __name__ == "__main__":
    main()