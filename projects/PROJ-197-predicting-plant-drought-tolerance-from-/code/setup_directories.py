"""
Script to initialize the project directory structure.
This script creates the required directories for the llmXive pipeline.
"""
import os
from pathlib import Path

def main():
    """Create the standard project directory structure."""
    # Define the root directory (current working directory or project root)
    root = Path(".")
    
    # Define the required directories based on the task specification
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "tests",
        "docs",
        "docs/reports",
        "data/logs",  # Required for T030 metrics.json
        "figures"     # Commonly needed for plots
    ]
    
    created_count = 0
    for dir_name in directories:
        dir_path = root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")
    
    print(f"\nTotal directories created: {created_count}")
    print("Project directory structure initialization complete.")

if __name__ == "__main__":
    main()