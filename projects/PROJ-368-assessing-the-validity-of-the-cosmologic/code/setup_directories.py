"""
Module to create the required project directory structure.
Implements T004: Create all project directories.
"""
import os
import sys
from pathlib import Path

def create_directories(base_path: Path = None) -> None:
    """
    Creates the required project directory structure.
    
    Directories created:
    - data/raw
    - data/processed
    - data/simulations
    - data/reports
    - code (if not already present)
    - tests (if not already present)
    
    Args:
        base_path: Base path for the project. Defaults to current working directory.
    """
    if base_path is None:
        base_path = Path.cwd()
    
    # Define the directory structure relative to base_path
    directories = [
        "data/raw",
        "data/processed",
        "data/simulations",
        "data/reports",
        "code",
        "tests"
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = base_path / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"\nDirectory creation complete. {created_count} new directories created.")
    
    # Verification step: list the structure
    print("\nVerification: Current directory structure:")
    print("-" * 40)
    for dir_path in directories:
        full_path = base_path / dir_path
        if full_path.exists():
            print(f"[OK] {full_path}")
        else:
            print(f"[MISSING] {full_path}")
    print("-" * 40)

def main():
    """Main entry point for directory creation."""
    print("Starting project directory setup (Task T004)...")
    create_directories()
    print("Setup complete.")

if __name__ == "__main__":
    main()
