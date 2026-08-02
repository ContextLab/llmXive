"""
Script to create the required directory structure for the llmXive project.
This script ensures all necessary folders exist for data storage, code organization,
and model artifacts.
"""
import os
import sys

def create_directories():
    """Create the project directory structure."""
    # Define the directories to create relative to the project root
    directories = [
        "code",
        "code/utils",
        "code/tests",
        "data/raw",
        "data/processed",
        "data/results",
        "artifacts/models"
    ]

    created_count = 0
    for dir_path in directories:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")

    print(f"\nTotal directories created: {created_count}")
    print("Directory structure setup complete.")

if __name__ == "__main__":
    create_directories()
