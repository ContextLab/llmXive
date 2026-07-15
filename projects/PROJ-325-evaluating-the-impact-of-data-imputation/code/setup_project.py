"""
Setup script to initialize the project directory structure.
Creates the required folders as per the implementation plan.
"""
import os
from pathlib import Path

def main():
    root = Path(".")
    
    # Define the directory structure to create
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "tests",
        "specs/contracts",
        "state",
        "figures"
    ]

    created_count = 0
    for dir_path in directories:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")

    print(f"Setup complete. Created {created_count} new directories.")

if __name__ == "__main__":
    main()
