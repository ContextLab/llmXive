"""
create_code_structure.py

This script creates the required code directory hierarchy for the project and ensures
that each directory is a Python package by adding an empty ``__init__.py`` file.
It is intended to be run as a module (``python -m create_code_structure``) or
imported and called from the test suite.
"""

import os
import sys
from pathlib import Path
from typing import List

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def ensure_directory(dir_path: Path) -> None:
    """
    Ensure that ``dir_path`` exists as a directory.
    Creates parent directories as needed.
    """
    dir_path.mkdir(parents=True, exist_ok=True)


def create_init_file(dir_path: Path) -> None:
    """
    Create an empty ``__init__.py`` file inside ``dir_path`` so that the
    directory is recognised as a Python package.
    """
    init_file = dir_path / "__init__.py"
    if not init_file.exists():
        init_file.touch()


# ----------------------------------------------------------------------
# Main routine
# ----------------------------------------------------------------------
def main() -> None:
    """
    Create the required code directories and ``__init__`` files.
    """
    # Directories are defined relative to the repository root.
    repo_root = Path(__file__).resolve().parents[1]  # ``code/`` -> repo root
    target_dirs: List[Path] = [
        repo_root / "src" / "lib",
        repo_root / "src" / "metrics",
        repo_root / "src" / "experiment",
        repo_root / "src" / "analysis",
        repo_root / "tests",
    ]

    for d in target_dirs:
        ensure_directory(d)
        create_init_file(d)

    # Also ensure that the top‑level ``src`` package has an ``__init__.py``.
    src_dir = repo_root / "src"
    ensure_directory(src_dir)
    create_init_file(src_dir)

    # ``tests`` is already a package due to the ``__init__`` file we create above.


if __name__ == "__main__":
    # When executed as a script we add the repository root to ``sys.path``
    # so that any relative imports work correctly.
    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root))
    main()
