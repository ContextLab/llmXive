"""
Setup script to initialize the project directory structure.
Creates the required directories for code, data, and tests as per project specifications.
"""
import os
from pathlib import Path

def setup_directories():
    """Create the project directory structure."""
    # Define the base directory (project root)
    base_dir = Path(__file__).resolve().parent.parent

    # Define the directory structure to create
    directories = [
        # Code structure
        base_dir / "code",
        base_dir / "code" / "data",
        base_dir / "code" / "analysis",
        base_dir / "code" / "utils",
        
        # Data structure
        base_dir / "data",
        base_dir / "data" / "raw",
        base_dir / "data" / "processed",
        base_dir / "data" / "artifacts",
        
        # Tests structure
        base_dir / "tests",
        base_dir / "tests" / "contract",
        base_dir / "tests" / "integration",
        base_dir / "tests" / "unit"
    ]

    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory}")
            created_count += 1
        else:
            print(f"Directory already exists: {directory}")

    print(f"\nSetup complete. Created {created_count} new directories.")
    return True

if __name__ == "__main__":
    setup_directories()