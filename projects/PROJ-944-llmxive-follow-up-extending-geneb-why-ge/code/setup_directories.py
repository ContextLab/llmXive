"""
Setup directory structure for the llmXive automated science pipeline.
Creates necessary directories for data, outputs, and state management.
"""
import os
import sys
from pathlib import Path


def setup_directories():
    """
    Create the required directory structure for the project.
    
    Creates:
    - data/raw/
    - data/processed/
    - outputs/reports/
    - outputs/figures/
    - state/
    """
    # Define the project root relative to the code directory
    # Assuming this script is run from the project root or code/ directory
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent if current_dir.name == "code" else current_dir

    # Define relative paths to create
    directories = [
        "data/raw",
        "data/processed",
        "outputs/reports",
        "outputs/figures",
        "state"
    ]

    created_count = 0
    skipped_count = 0

    for dir_path in directories:
        full_path = project_root / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            if full_path.is_dir():
                created_count += 1
                print(f"Created directory: {full_path}")
            else:
                print(f"Warning: Path exists but is not a directory: {full_path}", file=sys.stderr)
        except PermissionError:
            print(f"Error: Permission denied creating directory: {full_path}", file=sys.stderr)
        except Exception as e:
            print(f"Error creating directory {full_path}: {e}", file=sys.stderr)

    print(f"\nDirectory setup complete. Created: {created_count}, Skipped/Exists: {skipped_count}")
    return created_count == len(directories)


def main():
    """Entry point for the setup_directories script."""
    success = setup_directories()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()