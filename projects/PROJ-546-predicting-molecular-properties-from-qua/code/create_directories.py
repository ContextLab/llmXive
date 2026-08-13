"""
Script to create the required directory structure for the project.
Implements task T001b.
"""
import os
from pathlib import Path

def create_directories():
    """
    Creates the following directories relative to the project root:
    - data/raw/
    - data/optimized_geometries/
    - logs/
    - reports/
    - contracts/
    - docs/
    """
    # Define the base project root. Assuming the script is run from the project root
    # or the current working directory is the project root.
    base_path = Path.cwd()
    
    directories = [
        "data/raw",
        "data/optimized_geometries",
        "logs",
        "reports",
        "contracts",
        "docs"
    ]
    
    created_count = 0
    for dir_name in directories:
        full_path = base_path / dir_name
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"Directory setup complete. {created_count} new directories created.")
    return True

def main():
    """Entry point for the script."""
    success = create_directories()
    if success:
        print("Task T001b completed successfully.")
    else:
        print("Task T001b failed.")
        exit(1)

if __name__ == "__main__":
    main()