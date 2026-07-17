"""
Script to create the project directory structure as defined in plan.md.
This script ensures all required directories exist before any data generation or execution.
"""
import os
from pathlib import Path

def main():
    root = Path(".")
    
    # Define the required directories based on plan.md
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/results",
        "tests",
        "contracts"
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
    
    print(f"\nProject structure setup complete. {created_count} new directories created.")

if __name__ == "__main__":
    main()