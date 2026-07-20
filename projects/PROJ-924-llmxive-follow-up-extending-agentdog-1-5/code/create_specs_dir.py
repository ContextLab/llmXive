"""
Script to create the `specs/` directory for the project.
This task (T001f) ensures the directory structure for specification documents exists.
"""
import os
from pathlib import Path

def ensure_specs_directory():
    """
    Creates the `specs/` directory if it does not already exist.
    Returns the Path object of the created/existing directory.
    """
    # Define the project root relative to this script's location or use a standard base
    # Assuming the script is run from the project root or the path is constructed correctly
    project_root = Path(__file__).resolve().parent.parent
    specs_dir = project_root / "specs"

    if not specs_dir.exists():
        specs_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {specs_dir}")
    else:
        print(f"Directory already exists: {specs_dir}")

    return specs_dir

def main():
    """Main entry point for T001f."""
    try:
        specs_path = ensure_specs_directory()
        # Verify creation
        if specs_path.exists() and specs_path.is_dir():
            print(f"Success: {specs_path} is ready.")
            return 0
        else:
            print(f"Error: Failed to create or verify {specs_path}")
            return 1
    except Exception as e:
        print(f"Error during directory creation: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
