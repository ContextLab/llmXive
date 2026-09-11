"""
Script to create the project directory structure.
This script is for documentation and future automation only.
"""
import os
import sys
from pathlib import Path

def main():
    """Create the required directory structure."""
    # Define the base directory (project root)
    base_dir = Path(__file__).resolve().parent.parent
    
    # List of directories to create relative to the project root
    directories = [
        "code",
        "data",
        "data/raw",
        "data/processed",
        "data/logs",
        "tests",
        "artifacts",
        "figures"
    ]
    
    # Create each directory
    for dir_path in directories:
        full_path = base_dir / dir_path
        os.makedirs(full_path, exist_ok=True)
        print(f"Created directory: {full_path}")
    
    print("Directory structure creation complete.")

if __name__ == "__main__":
    main()
