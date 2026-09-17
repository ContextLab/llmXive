"""
Script to initialize the project directory structure for llmXive follow-up.
Creates all required directories under the project root.
"""
import os
import sys

def create_directories():
    """Create the standard project directory structure."""
    directories = [
        "src",
        "tests",
        "data",
        "contracts",
        "state",
        "logs",
        "templates",
        "data/raw",
        "data/processed",
        "data/samples",
        "src/gatekeeper",
        "src/utils",
        "src/cli",
        "tests/contract",
        "tests/integration",
        "tests/unit"
    ]

    created_count = 0
    for dir_path in directories:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")
    
    if created_count == 0:
        print("All directories already exist.")
    else:
        print(f"Successfully created {created_count} new directories.")

if __name__ == "__main__":
    create_directories()