"""
create_code_structure.py

Utility script to create the required code directory hierarchy for the project.
It ensures the following directories exist (relative to the project root):
  - src/
    - lib/
    - metrics/
    - experiment/
    - analysis/
  - tests/

For each Python package directory an empty ``__init__.py`` file is created so
that the directories are importable as packages.

The script is used by the test suite (see ``tests/test_structure.py``) via the
``main`` function. It can also be executed directly::

    python code/create_code_structure.py
"""

import os
from pathlib import Path
from typing import List

__all__ = ["ensure_directory", "create_init_file", "main"]

def ensure_directory(dir_path: Path) -> None:
    """
    Ensure a directory exists.

    Parameters
    ----------
    dir_path: Path
        The directory to create. Parents are created as needed.
    """
    dir_path.mkdir(parents=True, exist_ok=True)

def create_init_file(package_dir: Path) -> None:
    """
    Create an empty ``__init__.py`` file in ``package_dir`` if it does not already exist.

    Parameters
    ----------
    package_dir: Path
        The directory that should become a Python package.
    """
    init_path = package_dir / "__init__.py"
    if not init_path.exists():
        # Touch the file – it will be empty but marks the directory as a package.
        init_path.touch()

def _project_root() -> Path:
    """
    Resolve the project root directory. This file lives under ``code/`` so the
    project root is two levels up from this file.
    """
    return Path(__file__).resolve().parents[1]

def main() -> None:
    """
    Create the required directory hierarchy and ``__init__.py`` files.
    """
    root = _project_root()

    # Define the package directories that need to exist.
    src_dir = root / "src"
    package_subdirs: List[Path] = [
        src_dir / "lib",
        src_dir / "metrics",
        src_dir / "experiment",
        src_dir / "analysis",
    ]

    # Create each package directory and its __init__.py.
    for pkg_dir in package_subdirs:
        ensure_directory(pkg_dir)
        create_init_file(pkg_dir)

    # Ensure the top‑level ``src`` package also has an ``__init__.py``.
    ensure_directory(src_dir)
    create_init_file(src_dir)

    # Ensure the tests directory exists (it is not a package, but we keep it for consistency).
    tests_dir = root / "tests"
    ensure_directory(tests_dir)

    # Optionally, create a placeholder ``__init__.py`` in tests so that
    # imports from tests work in some environments. This is harmless.
    create_init_file(tests_dir)

if __name__ == "__main__":
    # When executed as a script, run the creation routine.
    main()