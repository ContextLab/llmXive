"""
Script to create the required directory structure for the project.
This script ensures all directories specified in docs/design/directory_structure.md exist.
"""
import os
import sys
from pathlib import Path

def create_directories():
    """Create the directory structure defined in the specification."""
    # Define the base directory (project root)
    base_dir = Path(__file__).resolve().parent.parent
    
    # Define the required directory structure relative to the base
    directories = [
        "data/raw",
        "data/derived/topology",
        "data/derived/vdos",
        "data/derived/reference",
        "data/derived/correlation",
        "data/metadata",
        "outputs/figures",
        "outputs/reports",
        "docs/design"
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
    
    return created_count

def main():
    """Main entry point."""
    print("Setting up project directory structure...")
    count = create_directories()
    print(f"Setup complete. Created {count} new directories.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
