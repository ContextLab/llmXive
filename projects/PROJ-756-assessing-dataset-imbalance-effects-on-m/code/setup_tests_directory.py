"""
Setup script to create the tests directory structure for the project.
Ensures the tests directory exists at the project root relative to the code folder.
"""
import os
import sys
from pathlib import Path

def create_tests_directory():
    """
    Creates the tests directory if it does not exist.
    Also creates standard subdirectories for unit, integration, and contract tests.
    """
    # Determine the project root (parent of the code directory)
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    project_root = code_dir.parent

    tests_dir = project_root / "tests"
    
    if not tests_dir.exists():
        tests_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {tests_dir}")
    else:
        print(f"Directory already exists: {tests_dir}")

    # Create standard subdirectories
    subdirs = ["unit", "integration", "contract", "fixtures"]
    for subdir in subdirs:
        subdir_path = tests_dir / subdir
        if not subdir_path.exists():
            subdir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created subdirectory: {subdir_path}")
        else:
            print(f"Subdirectory already exists: {subdir_path}")

    # Create __init__.py files to make them proper Python packages
    for subdir_path in [tests_dir] + [tests_dir / d for d in subdirs]:
        init_file = subdir_path / "__init__.py"
        if not init_file.exists():
            init_file.touch()
            print(f"Created {init_file}")

    return True

def main():
    """Main entry point for the script."""
    try:
        success = create_tests_directory()
        if success:
            print("Tests directory structure setup complete.")
            sys.exit(0)
        else:
            print("Failed to setup tests directory.")
            sys.exit(1)
    except Exception as e:
        print(f"Error during setup: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
