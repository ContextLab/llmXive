"""
Project structure initialization script for the Submarine Hydrothermal Vent Microbial Communities project.
Creates the required directory hierarchy as specified in the implementation plan.
"""
import os
from pathlib import Path


def main():
    """Create the project directory structure."""
    # Define the project root (current directory)
    root = Path(".")

    # Define the required directories relative to the project root
    directories = [
        "data/raw",
        "data/processed",
        "code",
        "tests",
        "state",
        "results/figures",
    ]

    # Create directories
    created_count = 0
    for dir_path in directories:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")

    # Create __init__.py files to make directories into Python packages where applicable
    # Only for 'code' and 'tests' as they are Python package directories
    init_files = [
        root / "code" / "__init__.py",
        root / "tests" / "__init__.py",
        root / "tests" / "contract" / "__init__.py",
        root / "tests" / "integration" / "__init__.py",
    ]

    for init_file in init_files:
        # Ensure parent directory exists before creating __init__.py
        if init_file.parent.exists():
            if not init_file.exists():
                init_file.touch()
                print(f"Created: {init_file}")
            else:
                print(f"File already exists: {init_file}")

    print(f"\nProject structure initialization complete. Created {created_count} new directories.")
    print("Directory structure:")
    for dir_path in directories:
        print(f"  {dir_path}/")


if __name__ == "__main__":
    main()
