"""
Project Structure Creation Script

This script creates the directory structure required for the
Gut Microbiome-Cognitive Correlation Study project.
"""

import os
from pathlib import Path


def main():
    """Create the project directory structure."""
    # Define the base directory (project root)
    base_dir = Path(".")

    # Define the directory structure to create
    directories = [
        "code/utils",
        "code/models",
        "data/raw",
        "data/processed",
        "data/interim",
        "results/associations",
        "results/plots",
        "results/sensitivity",
        "results/power",
        "tests",
    ]

    created_dirs = []
    for dir_path in directories:
        full_path = base_dir / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(full_path))
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")

    if not created_dirs:
        print("All directories already exist.")
    else:
        print(f"\nSuccessfully created {len(created_dirs)} directories.")

    # Verify the structure
    print("\nVerifying directory structure:")
    for dir_path in directories:
        full_path = base_dir / dir_path
        exists = "✓" if full_path.exists() else "✗"
        print(f"{exists} {full_path}")


if __name__ == "__main__":
    main()