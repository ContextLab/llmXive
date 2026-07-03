"""
Script to create the test directory structure for the project.
Ensures all required test directories exist for contract, integration, and unit tests.
"""
import os
import sys
from pathlib import Path

def create_test_directories():
    """
    Creates the following directory structure under the project root:
    - tests/
    - tests/contract/
    - tests/integration/
    - tests/unit/

    Also creates a .gitkeep file in each to ensure they are tracked by git.
    """
    project_root = Path(__file__).resolve().parent.parent
    base_test_dir = project_root / "tests"

    directories = [
        base_test_dir,
        base_test_dir / "contract",
        base_test_dir / "integration",
        base_test_dir / "unit",
    ]

    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            # Create .gitkeep to ensure empty directories are tracked
            gitkeep = directory / ".gitkeep"
            gitkeep.touch()
            print(f"Created directory: {directory.relative_to(project_root)}")
            created_count += 1
        else:
            print(f"Directory already exists: {directory.relative_to(project_root)}")

    if created_count == 0:
        print("No new directories were created. All test directories already exist.")
    else:
        print(f"Successfully created {created_count} test directory(ies).")

    return True

def main():
    """Entry point for the script."""
    try:
        success = create_test_directories()
        if success:
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception as e:
        print(f"Error creating test directories: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
