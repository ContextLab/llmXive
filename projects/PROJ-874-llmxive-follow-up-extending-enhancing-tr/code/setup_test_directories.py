"""
Setup script to create the required test directory structure.
This script creates the following directories under the project root:
- tests/contract/
- tests/integration/
- tests/unit/
"""
import os
import sys
from pathlib import Path

def create_test_directories():
    """Create the required test directory structure."""
    # Determine the project root (parent of the code directory)
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent

    # Define the test directories to create
    test_dirs = [
        project_root / "tests" / "contract",
        project_root / "tests" / "integration",
        project_root / "tests" / "unit",
    ]

    # Create directories
    created_dirs = []
    for dir_path in test_dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
        created_dirs.append(str(dir_path.relative_to(project_root)))
        print(f"Created directory: {dir_path}")

    # Create __init__.py files to make them proper Python packages
    for dir_path in test_dirs:
        init_file = dir_path / "__init__.py"
        init_file.touch()
        print(f"Created package marker: {init_file}")

    return created_dirs

def main():
    """Main entry point."""
    print("Setting up test directory structure...")
    try:
        created = create_test_directories()
        print(f"\nSuccessfully created {len(created)} test directories:")
        for d in created:
            print(f"  - {d}")
        print("\nTest directory structure is ready.")
    except Exception as e:
        print(f"Error creating test directories: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
