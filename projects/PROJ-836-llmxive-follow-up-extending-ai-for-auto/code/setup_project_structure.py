"""
Script to initialize the llmXive project directory structure.
Creates the required folders for code, data, tests, config, and output.
"""
import os
from pathlib import Path

def main():
    root = Path(".")
    
    # Define the directory structure relative to the project root
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "tests/unit",
        "tests/integration",
        "config",
        "output",
        "figures"  # Added for potential figure outputs as per standard conventions
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
    
    print(f"\nProject structure initialization complete. {created_count} new directories created.")

if __name__ == "__main__":
    main()
