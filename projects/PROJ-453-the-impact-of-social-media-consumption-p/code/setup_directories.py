"""
Project Directory Initialization Script for PROJ-453.

This script creates the required directory structure for the research project.
It ensures all necessary folders for data, code, results, tests, and contracts exist.
"""
import os
from pathlib import Path

# Define the project root based on the task description
# The task specifies creating directories in 'projects/PROJ-453-the-impact-of-social-media-consumption-p'
PROJECT_ROOT = Path("projects/PROJ-453-the-impact-of-social-media-consumption-p")

# Define the relative paths to be created
DIRECTORIES = [
    "data/raw",
    "data/processed",
    "code",
    "results/models",
    "results/figures",
    "tests",
    "contracts"
]

def main():
    print(f"Initializing project structure at: {PROJECT_ROOT.resolve()}")
    
    # Ensure the base project directory exists
    PROJECT_ROOT.mkdir(parents=True, exist_ok=True)

    created_count = 0
    skipped_count = 0

    for dir_path in DIRECTORIES:
        full_path = PROJECT_ROOT / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            if full_path.is_dir():
                created_count += 1
                print(f"Created/Verified directory: {full_path}")
        except OSError as e:
            print(f"Error creating directory {full_path}: {e}")
            raise

    print(f"\nSetup complete. {created_count} directories verified/created.")
    print(f"Project root: {PROJECT_ROOT}")

if __name__ == "__main__":
    main()