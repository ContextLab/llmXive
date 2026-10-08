"""
Script to create test directory structure for the project.
Implements task T001d: Create `tests/unit/` and `tests/integration/` directories.
"""
import os
from pathlib import Path


def setup_test_directories():
    """
    Creates the required test directory structure:
    - tests/unit/
    - tests/integration/

    Returns:
        None
    """
    project_root = Path(__file__).resolve().parent.parent
    tests_base = project_root / "tests"
    unit_dir = tests_base / "unit"
    integration_dir = tests_base / "integration"

    # Create directories if they don't exist
    unit_dir.mkdir(parents=True, exist_ok=True)
    integration_dir.mkdir(parents=True, exist_ok=True)

    # Create __init__.py files to make them proper Python packages
    (unit_dir / "__init__.py").touch()
    (integration_dir / "__init__.py").touch()

    print(f"Created directories: {unit_dir}, {integration_dir}")


if __name__ == "__main__":
    setup_test_directories()
