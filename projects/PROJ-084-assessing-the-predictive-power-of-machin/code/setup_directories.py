"""
Project Directory Initialization Script.

Creates the standard directory structure for the llmXive science pipeline:
- code/
- data/raw/
- data/processed/
- data/results/
- tests/

This script ensures the project tree is ready for artifact generation.
"""
import os
from pathlib import Path


def main():
    """Create all required project directories."""
    root = Path(".")
    
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/results",
        "tests"
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
    
    print(f"Setup complete. {created_count} new directories created.")


if __name__ == "__main__":
    main()