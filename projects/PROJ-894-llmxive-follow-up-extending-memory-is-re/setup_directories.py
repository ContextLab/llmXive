"""
Script to create the project directory structure for PROJ-894.
This script ensures all required directories exist as per the implementation plan.
"""
import os
from pathlib import Path

def create_directories():
    """Create the full project directory structure."""
    base_path = Path(__file__).parent

    # Define all required directories
    directories = [
        "code",
        "data",
        "tests",
        "data/raw",
        "data/intermediate",
        "data/processed",
        "data/processed/graphs",
        "data/processed/results",
    ]

    # Create each directory
    for dir_path in directories:
        full_path = base_path / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path.relative_to(base_path)}")

    print("\nDirectory structure setup complete.")
    print(f"Base path: {base_path}")

if __name__ == "__main__":
    create_directories()
