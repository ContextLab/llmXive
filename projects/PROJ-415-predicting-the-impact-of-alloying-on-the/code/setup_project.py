"""
Project Setup Script for PROJ-415-predicting-the-impact-of-alloying-on-the
Creates the required directory structure for the automated science pipeline.
"""
import os
import sys
from pathlib import Path

def create_directories():
    """Create the project directory structure as per implementation plan."""
    # Define the base directory (project root)
    base_dir = Path.cwd()
    
    # Define the required directories
    directories = [
        "code",
        "code/utils",
        "code/data",
        "code/models",
        "code/validation",
        "tests",
        "tests/unit",
        "tests/contract",
        "tests/integration",
        "data",
        "data/raw",
        "data/curated",
        "data/artifacts",
        "data/logs",
        "models",
        "reports",
        "figures"
    ]
    
    created_count = 0
    skipped_count = 0
    
    for dir_path in directories:
        full_path = base_dir / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
            skipped_count += 1
    
    print(f"\nSetup complete: {created_count} directories created, {skipped_count} already existed.")
    return True

def create_init_files():
    """Create __init__.py files to make directories Python packages."""
    base_dir = Path.cwd()
    package_dirs = [
        "code",
        "code/utils",
        "code/data",
        "code/models",
        "code/validation",
        "tests",
        "tests/unit",
        "tests/contract",
        "tests/integration"
    ]
    
    for dir_path in package_dirs:
        init_file = base_dir / dir_path / "__init__.py"
        if not init_file.exists():
            init_file.touch()
            print(f"Created __init__.py: {init_file}")
        else:
            print(f"__init__.py already exists: {init_file}")

def main():
    """Main entry point for project setup."""
    print("Starting project setup for PROJ-415...")
    
    try:
        create_directories()
        create_init_files()
        print("\nProject structure setup completed successfully.")
        return 0
    except Exception as e:
        print(f"\nError during project setup: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
