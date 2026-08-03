"""
Setup script to create the required project directory structure.
This script ensures all necessary folders for the llmXive pipeline exist.
"""
import os
from pathlib import Path

def main():
    """Create the root directory structure as defined in T001a."""
    # Define the root directory (current working directory or project root)
    root = Path(".")
    
    # Define the required directories relative to the root
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/models",
        "tests/unit",
        "tests/integration",
        "specs"
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"\nSetup complete. Created {created_count} new directories.")

if __name__ == "__main__":
    main()
