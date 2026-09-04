"""
Project setup script for PROJ-761.
Creates the required directory structure for the automated science pipeline.
"""
import os
import sys
from pathlib import Path

def main():
    """Create the project directory structure."""
    # Define the required directories relative to the project root
    # Assuming this script runs from the project root
    base_dir = Path.cwd()
    
    directories = [
        "data/raw",
        "data/processed",
        "code",
        "tests",
        "artifacts/logs",
        "artifacts/plots",
        "artifacts/reports",
        "contracts"
    ]
    
    created_count = 0
    existing_count = 0
    
    for dir_path in directories:
        full_path = base_dir / dir_path
        try:
            if full_path.exists():
                existing_count += 1
                print(f"Directory exists: {full_path}")
            else:
                full_path.mkdir(parents=True, exist_ok=True)
                created_count += 1
                print(f"Created directory: {full_path}")
        except OSError as e:
            print(f"Error creating directory {full_path}: {e}", file=sys.stderr)
            sys.exit(1)
    
    print(f"\nSetup complete: {created_count} directories created, {existing_count} already existed.")
    print("Project structure verified.")
    return 0

if __name__ == "__main__":
    sys.exit(main())