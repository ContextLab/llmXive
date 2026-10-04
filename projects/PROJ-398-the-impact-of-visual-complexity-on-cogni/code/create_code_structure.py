"""
create_code_structure.py

This module provides utilities to create the required source code directory
structure for the project. It is used by the test suite (tests/test_structure.py)
to verify that the expected directories exist.

Functions
----------
ensure_directory(path: Path) -> None
    Creates a directory (including parent directories) if it does not already exist.

create_init_file(dir_path: Path) -> None
    Creates an empty ``__init__.py`` file inside ``dir_path`` to make the directory
    a Python package. If the file already exists, it is left untouched.

main() -> None
    Creates the top‑level ``src`` sub‑packages (lib, metrics, experiment, analysis)
    and the top‑level ``tests`` directory. Each ``src/*`` directory receives an
    ``__init__.py`` file.
"""

import os
from pathlib import Path
from typing import List

def ensure_directory(path: Path) -> None:
    """
    Ensure that ``path`` exists as a directory.

    Parameters
    ----------
    path: Path
        The directory path to create.
    """
    # ``parents=True`` creates any missing parent directories.
    # ``exist_ok=True`` makes the operation idempotent.
    path.mkdir(parents=True, exist_ok=True)

def create_init_file(dir_path: Path) -> None:
    """
    Create an ``__init__.py`` file in ``dir_path`` if it does not already exist.

    Parameters
    ----------
    dir_path: Path
        The directory in which to create the ``__init__.py`` file.
    """
    init_file = dir_path / "__init__.py"
    if not init_file.exists():
        init_file.touch()

def main() -> None:
    """
    Create the required code directory structure:

    - src/lib/
    - src/metrics/
    - src/experiment/
    - src/analysis/
    - tests/
    """
    # Resolve the project root (the directory that contains the ``code`` folder).
    # This file lives in ``code/create_code_structure.py``; the project root is its
    # grand‑parent directory.
    project_root = Path(__file__).resolve().parents[1]

    # Define the directories relative to the project root.
    src_subdirs: List[Path] = [
        project_root / "src" / "lib",
        project_root / "src" / "metrics",
        project_root / "src" / "experiment",
        project_root / "src" / "analysis",
    ]
    test_dir = project_root / "tests"

    # Create each src sub‑directory and its ``__init__.py``.
    for subdir in src_subdirs:
        ensure_directory(subdir)
        create_init_file(subdir)

    # Create the top‑level tests directory (also a package for consistency).
    ensure_directory(test_dir)
    create_init_file(test_dir)

    # Optionally, create the top‑level ``src`` package ``__init__.py`` if it does
    # not already exist. This makes ``src`` importable as a package.
    src_root = project_root / "src"
    ensure_directory(src_root)
    create_init_file(src_root)

if __name__ == "__main__":
    # When executed directly, run the directory‑creation routine.
    main()