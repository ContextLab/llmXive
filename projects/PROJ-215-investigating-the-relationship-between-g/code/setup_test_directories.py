"""
Script to create the required test directory structure for the project.
Implements Task T001c: Create test directories.
"""
import os
import sys
from pathlib import Path

def main():
    """
    Creates the following directories:
    - tests/unit/
    - tests/integration/
    - tests/contract/
    """
    project_root = Path(__file__).resolve().parent.parent
    tests_root = project_root / "tests"

    required_dirs = [
        tests_root / "unit",
        tests_root / "integration",
        tests_root / "contract",
    ]

    created_count = 0
    for dir_path in required_dirs:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")

    if created_count > 0:
        print(f"Successfully created {created_count} new test directories.")
    else:
        print("All required test directories already existed.")
    
    # Ensure __init__.py files exist to make them proper Python packages
    init_file = tests_root / "__init__.py"
    if not init_file.exists():
        init_file.touch()
        print(f"Created {init_file}")
    
    for dir_path in required_dirs:
        init_file = dir_path / "__init__.py"
        if not init_file.exists():
            init_file.touch()
            print(f"Created {init_file}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
