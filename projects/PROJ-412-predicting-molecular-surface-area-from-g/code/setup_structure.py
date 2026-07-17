"""
Script to setup the project directory structure.
Creates all required directories for code, data, and results.
"""
import os
import sys
from pathlib import Path

def main():
    """Create the project directory structure."""
    # Define the project root (current directory)
    project_root = Path.cwd()

    # Define all required directories
    directories = [
        # Code directories
        "code",
        "code/data",
        "code/models",
        "code/eval",
        "code/utils",
        
        # Data directories
        "data/raw",
        "data/processed",
        "data/splits",
        
        # Results directories
        "results",
        "results/reports",
        "results/plots",
        
        # Test directories
        "tests",
        "tests/contract",
        "tests/unit",
        "tests/integration",
    ]

    # Create directories
    created_count = 0
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")

    print(f"\nSetup complete. Created {created_count} new directories.")
    print(f"Project root: {project_root}")

    # Verify structure
    print("\nVerifying directory structure:")
    all_exist = True
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            print(f"  ERROR: Missing {full_path}")
            all_exist = False
        else:
            print(f"  OK: {full_path}")

    if all_exist:
        print("\nAll directories successfully created/verified.")
        return 0
    else:
        print("\nSome directories are missing. Please check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())