"""
Project structure creation script.

This script creates the required directory hierarchy for the
chess Elo analysis project. It can be executed directly or imported
and called via ``create_directories()``.
"""

import sys
from pathlib import Path

def create_directories() -> None:
    """
    Create all required project directories.

    The function is idempotent – existing directories are left untouched.
    """
    # Determine the project root (the directory containing the ``code`` folder)
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent

    # List of directories relative to the project root
    required_dirs = [
        "src",
        "tests",
        "data",
        "specs",
        "data/raw",
        "data/processed",
        "data/results",
        "specs/contracts",
        "tests/contract",
        "tests/unit",
        "tests/integration",
    ]

    for rel_dir in required_dirs:
        dir_path = project_root / rel_dir
        dir_path.mkdir(parents=True, exist_ok=True)

    print("Project directories created successfully.")

if __name__ == "__main__":
    # When executed as a script, run the creation routine
    create_directories()
    sys.exit(0)
