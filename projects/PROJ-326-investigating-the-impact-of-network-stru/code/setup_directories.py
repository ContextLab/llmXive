"""
Script to create the project directory structure for llmXive.
This script creates all required directories under the project root.
"""
import os
from pathlib import Path

def main():
    # Define the project root (current directory where script is run)
    root = Path(__file__).parent.parent

    # Define the directory structure relative to the root
    directories = [
        "code",
        "code/src",
        "code/src/generators",
        "code/src/simulation",
        "code/src/analysis",
        "code/src/utils",
        "code/tests",
        "data/raw",
        "data/analysis",
        "paper"
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

    print(f"Directory setup complete. Created {created_count} new directories.")

if __name__ == "__main__":
    main()
