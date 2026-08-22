"""
Script to create the project directory structure for the plant root architecture prediction pipeline.

This script ensures deterministic creation of required directories using os.makedirs.
"""
import os
from pathlib import Path

def main():
    """Create all required project directories."""
    # Define the project root (current directory context)
    root = Path(".")
    
    # Define the directory structure to create
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
    
    for dir_path in directories:
        full_path = root / dir_path
        os.makedirs(full_path, exist_ok=True)
        print(f"Created directory: {full_path}")
    
    print("Directory structure setup complete.")

if __name__ == "__main__":
    main()