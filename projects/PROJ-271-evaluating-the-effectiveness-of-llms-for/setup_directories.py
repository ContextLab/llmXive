"""
Script to initialize the directory structure for the LLM Code Smell Detection project.
Creates data/raw, data/processed, and results directories relative to the project root.
"""
import os
from pathlib import Path

def main():
    # Define the project root based on the task context
    project_root = Path(__file__).resolve().parent

    # Define relative paths required by the task
    directories = [
        "data/raw",
        "data/processed",
        "results"
    ]

    created_count = 0
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")

    print(f"Directory initialization complete. {created_count} new directories created.")

if __name__ == "__main__":
    main()