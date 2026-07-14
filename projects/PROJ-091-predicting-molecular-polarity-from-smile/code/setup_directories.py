"""
Script to initialize the project directory structure for the molecular polarity prediction pipeline.
Creates all required directories as specified in the project plan.
"""
import os
from pathlib import Path

def main():
    """Create the standard project directory structure."""
    # Define the project root (current working directory or parent of code/)
    # Since this script lives in code/, we go up one level to find the project root
    project_root = Path(__file__).resolve().parent.parent
    
    # Define required directories relative to project root
    directories = [
        "code",
        "tests",
        "data",
        "data/raw",
        "data/processed",
        "data/processed/analysis",
        "logs"
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

    print(f"\nProject initialization complete. Created {created_count} new directories.")
    return 0

if __name__ == "__main__":
    exit(main())