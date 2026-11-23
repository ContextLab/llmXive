"""
Script to create the required top‑level code package directories for the project.

This script is intentionally lightweight and relies on the generic directory‑creation
helpers defined in ``create_code_structure.py``. It creates the following directories:

  - src/lib/
  - src/metrics/
  - src/experiment/
  - src/analysis/
  - tests/

For each package directory (everything under ``src``) an ``__init__.py`` file is
created so the directories are recognised as Python packages. The ``tests`` directory
is left without an ``__init__`` file because the test suite is discovered by pytest
without it.

The public entry point is ``main()`` which can be executed directly:
    python code/setup_code_directories.py
"""

import os
from pathlib import Path

# Re‑use the generic helpers from the existing module
from create_code_structure import ensure_directory, create_init_file

__all__ = ["create_code_structure", "main"]


def create_code_structure() -> None:
    """
    Create the required code package directories and initialise them as Python packages.
    """
    # Base ``src`` directory
    src_base = Path("src")

    # List of directories to create
    dirs_to_create = [
        src_base / "lib",
        src_base / "metrics",
        src_base / "experiment",
        src_base / "analysis",
        Path("tests"),
    ]

    for directory in dirs_to_create:
        # Ensure the directory exists
        ensure_directory(directory)

        # Initialise as a package (skip ``tests`` – pytest discovers it without __init__)
        if directory.name != "tests":
            create_init_file(directory)


def main() -> None:
    """
    Entry point for the script – simply forwards to ``create_code_structure``.
    """
    create_code_structure()


if __name__ == "__main__":
    # When executed as a script, create the directories immediately.
    main()
