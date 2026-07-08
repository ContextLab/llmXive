import os
from pathlib import Path

def main():
    """
    Creates the project directory structure for the statistical analysis of topic drift.
    This script ensures all required directories exist relative to the project root.
    """
    # Define the project root (assuming this script is in code/ or code/setup/)
    # We will create directories relative to the current working directory or a fixed root.
    # Based on the task description, we assume the script runs from the project root or
    # creates the structure relative to where it is executed.
    
    # However, the task says "Create directories src/, tests/, ..."
    # The prompt implies the project root is where these should be.
    # Let's assume the script is run from the project root.
    
    base_path = Path.cwd()
    
    directories = [
        "src",
        "tests",
        "data/raw",
        "data/processed",
        "results/figures",
        "results/stats",
        "docs"
    ]
    
    created_count = 0
    existing_count = 0
    
    for dir_path in directories:
        full_path = base_path / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
            existing_count += 1
    
    print(f"Project structure ready. Created: {created_count}, Existing: {existing_count}")

if __name__ == "__main__":
    main()
