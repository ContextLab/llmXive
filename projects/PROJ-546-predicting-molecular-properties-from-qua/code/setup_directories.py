"""
Script to create the required directory structure for the molecular properties project.
This implements task T001b.
"""
import os
from pathlib import Path

def main():
    """Create all required directories for the project."""
    # Define the project root relative to where this script is located or current working directory
    # Assuming this script is run from the project root: projects/PROJ-546-predicting-molecular-properties-from-qua/
    project_root = Path.cwd()

    # Define directories to create based on task T001b
    directories = [
        "data/raw",
        "data/optimized_geometries",
        "logs",
        "reports",
        "contracts",
        "docs"
    ]

    created_count = 0
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")

    print(f"Directory creation complete. {created_count} new directories created.")

if __name__ == "__main__":
    main()