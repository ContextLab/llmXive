"""
Setup script to initialize the project directory structure.
Creates necessary directories for data, code, and tests.
"""
import os
import sys
from pathlib import Path

def create_directories():
    """Create the required project directory structure."""
    base_dir = Path(__file__).parent.parent
    
    # Define directories to create
    directories = [
        "data/raw",
        "data/processed",
        "code/models",
        "code/analysis",
        "code/utils",
        "code/config",
        "tests/contract",
        "tests/unit",
        "tests/integration",
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = base_dir / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    # Create .gitkeep files in data directories to preserve structure in git
    data_dirs = ["data/raw", "data/processed"]
    for dir_path in data_dirs:
        full_path = base_dir / dir_path / ".gitkeep"
        full_path.touch()
        print(f"Created .gitkeep in: {full_path}")
    
    print(f"\nDirectory setup complete. Created {created_count} new directories.")
    return True

def main():
    """Main entry point for the setup script."""
    try:
        create_directories()
        print("SUCCESS: Project structure initialized.")
        return 0
    except Exception as e:
        print(f"ERROR: Failed to initialize project structure: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
