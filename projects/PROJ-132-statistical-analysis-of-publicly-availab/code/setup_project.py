"""
Project structure setup script for PROJ-132.
Creates the required directory hierarchy for data, models, analysis, and tests.
"""
import os
import sys
from pathlib import Path

def create_directories():
    """
    Creates the standard project directory structure.
    Directories created:
    - src/data, src/models, src/analysis
    - data/raw, data/processed, data/interim
    - tests/contract, tests/unit, tests/integration
    - docs
    """
    project_root = Path(__file__).parent.parent
    base_dirs = [
        "src/data",
        "src/models",
        "src/analysis",
        "data/raw",
        "data/processed",
        "data/interim",
        "tests/contract",
        "tests/unit",
        "tests/integration",
        "docs"
    ]

    created_count = 0
    for dir_path in base_dirs:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")

    print(f"Project structure setup complete. {created_count} new directories created.")
    return True

def main():
    """Entry point for the setup script."""
    try:
        create_directories()
        return 0
    except Exception as e:
        print(f"Error during setup: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())