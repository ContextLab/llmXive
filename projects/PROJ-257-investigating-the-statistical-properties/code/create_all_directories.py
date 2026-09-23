"""
Script to create the complete project directory structure for T001.
This creates all directories required by the statistical properties project.
"""
import os
from pathlib import Path

def create_directories():
    """Create all required project directories."""
    base_path = Path.cwd()

    # Define all required directories
    directories = [
        "src",
        "tests",
        "data/raw",
        "data/processed",
        "output/results",
        "output/figures",
        "logs",
        "src/data",
        "src/analysis",
        "src/viz",
        "src/utils",
        "tests/unit",
        "tests/integration",
        "tests/contract"
    ]

    created_count = 0
    for dir_path in directories:
        full_path = base_path / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created: {full_path}")
            created_count += 1
        else:
            print(f"Exists: {full_path}")

    print(f"\nTotal directories created: {created_count}")
    return created_count

def main():
    create_directories()

if __name__ == "__main__":
    main()
