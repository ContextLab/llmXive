"""
Script to create the project directory structure as defined in plan.md.
This script creates the necessary folders for the llmXive project.
"""
import os
from pathlib import Path

def main():
    # Define the project root (assuming this script is run from the project root)
    # If run from code/, we need to adjust. The standard is to run from root.
    root = Path.cwd()
    
    # Define the relative paths to create
    paths = [
        "code",
        "code/data",
        "code/geometry",
        "code/analysis",
        "code/tests",
        "code/tests/unit",
        "code/tests/integration",
        "data/raw",
        "data/processed",
    ]

    created_count = 0
    for rel_path in paths:
        full_path = root / rel_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created: {full_path}")
            created_count += 1
        else:
            print(f"Exists: {full_path}")

    print(f"\nTotal directories created: {created_count}")
    print("Project structure initialization complete.")

if __name__ == "__main__":
    main()