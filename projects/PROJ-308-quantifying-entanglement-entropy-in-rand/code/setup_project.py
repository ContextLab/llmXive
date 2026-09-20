"""
Project Initialization Script for PROJ-308-quantifying-entanglement-entropy-in-rand.

This script creates the required directory structure for the project as specified
in task T001. It ensures all necessary folders for code, data, state, tests,
and documentation are present.
"""

import os
import sys
from pathlib import Path


def main():
    """
    Initialize the project directory structure.

    Creates the following directories relative to the project root:
    - code/
    - data/
      - raw/
      - processed/
    - state/
      - projects/
    - tests/
      - unit/
      - integration/
    - docs/
    - tools/
    """
    # Determine the project root.
    # We assume this script is located at <root>/code/setup_project.py
    # So we go up one level to get the root.
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent

    print(f"Initializing project structure at: {project_root}")

    # Define the directory structure to create
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "state",
        "state/projects",
        "tests/unit",
        "tests/integration",
        "docs",
        "tools",
    ]

    created_count = 0
    existing_count = 0

    for dir_path in directories:
        full_path = project_root / dir_path
        if full_path.exists():
            print(f"  [SKIP] {dir_path} (already exists)")
            existing_count += 1
        else:
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"  [CREATE] {dir_path}")
            created_count += 1

    print(f"\nInitialization complete.")
    print(f"  Created: {created_count} directories")
    print(f"  Skipped: {existing_count} directories (already existed)")

    # Verify structure
    print("\nVerifying directory structure...")
    missing = []
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.is_dir():
            missing.append(dir_path)

    if missing:
        print(f"  [ERROR] The following directories were not created: {missing}")
        sys.exit(1)
    else:
        print("  [OK] All required directories verified.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
