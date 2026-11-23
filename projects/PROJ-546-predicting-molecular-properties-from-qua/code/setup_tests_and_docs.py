"""
Task T001c: Create tests/ directory structure and docs/ directory.

This script creates the required directory hierarchy for the project:
- tests/unit/
- tests/integration/
- tests/contract/
- docs/

It also creates a placeholder __init__.py in each test subdirectory to ensure
they are recognized as Python packages.
"""
import os
from pathlib import Path

def create_directory_structure(base_path: Path) -> None:
    """Create the required directory structure for tests and docs."""
    # Define the directories to create
    directories = [
        base_path / "tests" / "unit",
        base_path / "tests" / "integration",
        base_path / "tests" / "contract",
        base_path / "docs",
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")

def create_init_files(base_path: Path) -> None:
    """Create __init__.py files in test directories to make them packages."""
    test_dirs = [
        base_path / "tests",
        base_path / "tests" / "unit",
        base_path / "tests" / "integration",
        base_path / "tests" / "contract",
    ]

    for directory in test_dirs:
        init_file = directory / "__init__.py"
        if not init_file.exists():
            init_file.touch()
            print(f"Created __init__.py in: {directory}")

def main() -> None:
    """Main entry point for the script."""
    # Determine the project root (assuming this script is in code/)
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent

    print(f"Project root: {project_root}")

    create_directory_structure(project_root)
    create_init_files(project_root)

    print("Directory structure creation complete.")
