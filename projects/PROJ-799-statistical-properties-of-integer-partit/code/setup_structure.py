"""
Project Setup Script for PROJ-799.
Creates the required directory structure for the integer partition research project.
"""
import os
import sys
from pathlib import Path

def main():
    """Create the directory structure for PROJ-799."""
    # Define the base project directory
    base_dir = Path("projects/PROJ-799-statistical-properties-of-integer-partit")
    
    # Define all required subdirectories
    directories = [
        "code",
        "code/utils",
        "data/raw",
        "data/processed",
        "data/schemas",
        "tests",
        "tests/data",
        "docs",
        "state/projects"
    ]
    
    # Create each directory
    created_count = 0
    for subdir in directories:
        dir_path = base_dir / subdir
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")
    
    print(f"\nSetup complete. Created {created_count} new directories.")
    print(f"Project structure rooted at: {base_dir}")
    
    # List the final structure
    print("\nFinal directory structure:")
    for dir_path in base_dir.rglob("*"):
        if dir_path.is_dir():
            print(f"  {dir_path.relative_to(base_dir)}")

if __name__ == "__main__":
    main()