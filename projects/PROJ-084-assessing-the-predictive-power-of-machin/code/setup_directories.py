"""
Script to initialize the project directory structure.
Creates standard folders for code, data (raw, processed, results), and tests.
"""
import os
from pathlib import Path

def main():
    # Define the project root (current directory)
    root = Path(".")
    
    # Define relative paths based on T001a requirements
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/results",
        "tests"
    ]
    
    created_count = 0
    for rel_path in directories:
        full_path = root / rel_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"\nSetup complete. {created_count} new directories created.")

if __name__ == "__main__":
    main()