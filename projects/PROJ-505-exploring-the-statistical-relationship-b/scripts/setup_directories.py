"""
Script to initialize the project directory structure for PROJ-505.
This script ensures all required directories exist as per the project plan.
"""
import os
from pathlib import Path

def create_directories():
    """Create the necessary directory structure for the project."""
    base_path = Path("projects/PROJ-505-exploring-the-statistical-relationship-b")
    
    # Directories to create
    directories = [
        "data",
        "data/raw",
        "data/processed",
        "data/artifacts",
        "code",
        "code/ingestion",
        "code/analysis",
        "code/utils",
        "tests",
        "tests/unit",
        "tests/integration"
    ]
    
    created_count = 0
    for dir_name in directories:
        full_path = base_path / dir_name
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"\nTotal new directories created: {created_count}")
    print("Directory structure initialization complete.")

if __name__ == "__main__":
    create_directories()
