"""
Project layout creation utilities.

This module provides functions to ensure that the required top‑level
directories and ``__init__.py`` files exist. It is used by the initial
bootstrap task (T001) to create a reproducible package structure.
"""

import os
from pathlib import Path

# List of top‑level directories that must exist in the repository root
REQUIRED_DIRS = [
    "code",
    "data",
    "docs",
    "tests",
    # Sub‑packages inside ``code`` that are part of the public API
    "code/utils",
    "code/data",
    "code/analysis",
    "code/models",
]

# Directories that should be recognised as Python packages
PACKAGE_DIRS = [
    "code",
    "code/utils",
    "code/data",
    "code/analysis",
    "code/models",
    "tests",
]


def ensure_directories() -> None:
    """
    Create all required directories if they do not already exist.

    The function is idempotent – calling it multiple times will not raise
    errors or overwrite existing content.
    """
    for dir_path in REQUIRED_DIRS:
        Path(dir_path).mkdir(parents=True, exist_ok=True)


def ensure_init_files() -> None:
    """
    Ensure that every package directory contains an ``__init__.py`` file.

    Empty ``__init__.py`` files are created where missing; existing files
    are left untouched.
    """
    for pkg_dir in PACKAGE_DIRS:
        init_path = Path(pkg_dir) / "__init__.py"
        if not init_path.is_file():
            init_path.touch()


def main() -> None:
    """
    Entry point for the layout script.

    Running this module as a script will create the directory tree and the
    required ``__init__.py`` files.
    """
    ensure_directories()
    ensure_init_files()


if __name__ == "__main__":
    main()
