"""
Script to create the required project directory structure.

Directories created:
  - data/raw/
  - data/processed/
  - data/analysis/
  - code/
  - tests/
  - docs/

The script is idempotent; running it multiple times will not raise errors.
"""

from __future__ import annotations

import sys

# Import the paths utility from llmxive_toolkit.
# This utility creates the folder if it does not exist.
from llmxive_toolkit import paths


def create_project_structure() -> None:
    """
    Ensure that all required top‑level project directories exist.
    """
    # Define the required directories using the paths helper.
    required_dirs = [
        paths.data("raw"),
        paths.data("processed"),
        paths.data("analysis"),
        paths.code(),
        paths.tests(),
        paths.docs(),
    ]

    for dir_path in required_dirs:
        # The Path object returned by paths.* creates the parent folder(s) if needed.
        dir_path.mkdir(parents=True, exist_ok=True)


def main(argv: list[str] | None = None) -> int:
    """
    Entry point for the script when executed from the command line.

    Returns:
        int: Exit code (0 for success, non‑zero for failure).
    """
    try:
        create_project_structure()
        print("Project directory structure created/verified.")
        return 0
    except Exception as e:
        print(f"Error creating project directories: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())