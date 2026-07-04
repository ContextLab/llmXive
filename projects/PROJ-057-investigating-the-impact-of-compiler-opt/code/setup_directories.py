"""
Setup script to create the required directory structure for the project.
This script ensures all necessary folders exist for code organization,
data storage, and testing.
"""
import os
import sys
from pathlib import Path


def create_directories():
    """Create the required directory structure."""
    # Define the base directory (current working directory or project root)
    base_path = Path(".")

    # Define the directory structure to create
    directories = [
        "code/kernels",
        "code/benchmarks",
        "code/analysis",
        "data/raw",
        "data/intermediates",
        "data/results",
        "tests",
    ]

    created_count = 0
    skipped_count = 0

    for dir_path in directories:
        full_path = base_path / dir_path
        try:
            if not full_path.exists():
                full_path.mkdir(parents=True, exist_ok=True)
                print(f"Created directory: {full_path}")
                created_count += 1
            else:
                # Check if it's actually a directory
                if full_path.is_dir():
                    print(f"Directory already exists: {full_path}")
                    skipped_count += 1
                else:
                    print(f"Error: Path exists but is not a directory: {full_path}")
                    return False
        except PermissionError:
            print(f"Error: Permission denied when creating {full_path}")
            return False
        except Exception as e:
            print(f"Error creating {full_path}: {e}")
            return False

    print(f"\nDirectory setup complete.")
    print(f"  Created: {created_count} directories")
    print(f"  Skipped (already existed): {skipped_count} directories")
    return True


def main():
    """Main entry point for the script."""
    print("Setting up project directory structure...")
    success = create_directories()

    if success:
        print("\nSuccess! All required directories are ready.")
        sys.exit(0)
    else:
        print("\nFailed to set up directory structure.")
        sys.exit(1)


if __name__ == "__main__":
    main()