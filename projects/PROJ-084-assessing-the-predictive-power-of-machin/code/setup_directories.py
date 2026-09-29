"""
Script to create the required project directory structure.
Implements T001a: Create code/, data/raw/, data/processed/, data/results/, tests/ directories.
"""
import os
from pathlib import Path

def main():
    """Create the standard project directory structure."""
    # Define the relative paths to be created
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/results",
        "tests"
    ]

    # Create directories and log the action
    for dir_path in directories:
        path = Path(dir_path)
        # Create parents if they don't exist (e.g., data/raw needs data/)
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {path.absolute()}")

    # Verification step: List created directories to provide evidence of completion
    print("\n--- Directory Structure Verification ---")
    for dir_path in directories:
        path = Path(dir_path)
        if path.exists() and path.is_dir():
            print(f"✓ {dir_path} exists")
        else:
            print(f"✗ {dir_path} missing (Unexpected)")
    print("----------------------------------------")

if __name__ == "__main__":
    main()