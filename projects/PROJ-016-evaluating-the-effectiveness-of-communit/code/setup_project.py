"""
Project setup script for llmXive automated science pipeline.
Creates the required directory structure for the project.
"""
import os
import sys
from pathlib import Path

def main():
    """Create the project directory structure."""
    # Define the base directory (project root)
    base_dir = Path(__file__).resolve().parent.parent

    # Define the directories to create
    directories = [
        "code/data",
        "code/analysis",
        "code/tests",
        "data/raw",
        "data/processed",
        "docs/output",
        "logs"
    ]

    # Create directories
    created_count = 0
    for dir_path in directories:
        full_path = base_dir / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")

    print(f"\nProject structure setup complete. {created_count} new directories created.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
