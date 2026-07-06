"""
Task T001: Create project directories structure.

Creates the following directories relative to the project root:
- src/
- tests/
- data/
- data/raw/
- data/processed/
- data/results/
- specs/
"""

import os
import sys
from pathlib import Path


def create_directories(base_path: Path) -> None:
    """Create the required project directory structure."""
    directories = [
        "src",
        "tests",
        "data",
        "data/raw",
        "data/processed",
        "data/results",
        "specs",
    ]

    created_count = 0
    skipped_count = 0

    for dir_path in directories:
        full_path = base_path / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
            skipped_count += 1

    print(f"\nSummary: {created_count} directories created, {skipped_count} already existed.")


def main() -> int:
    """Main entry point."""
    # Determine project root (current working directory)
    project_root = Path.cwd()

    print(f"Project root: {project_root}")
    print("Creating project directory structure...")

    create_directories(project_root)

    return 0


if __name__ == "__main__":
    sys.exit(main())