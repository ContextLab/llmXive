"""
setup_directories.py
--------------------

Utility module to create the required top‑level directory structure for the
project.  The function is deliberately tiny and has no side‑effects beyond
creating the directories; it can be safely re‑run (it will not raise if a
directory already exists).

The directories to be created are:

- data/raw/
- data/processed/
- code/
- tests/
- results/
- logs/
"""

import os
from pathlib import Path
from typing import List

# List of directories relative to the repository root that must exist.
REQUIRED_DIRS: List[Path] = [
    Path("data/raw"),
    Path("data/processed"),
    Path("code"),
    Path("tests"),
    Path("results"),
    Path("logs"),
]


def create_directory_structure() -> None:
    """
    Create the required directory structure for the project.

    The function iterates over :data:`REQUIRED_DIRS` and ensures each path
    exists as a directory.  Missing parents are created automatically
    (``parents=True``) and no error is raised if the directory already
    exists (``exist_ok=True``).

    This function is idempotent – calling it multiple times has the same
    effect as calling it once.
    """
    for directory in REQUIRED_DIRS:
        # Resolve the path relative to the current working directory.
        # ``mkdir`` with ``parents=True`` creates any missing ancestor
        # directories, and ``exist_ok=True`` silences the error if the
        # directory already exists.
        directory_path = Path.cwd() / directory
        directory_path.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    # When executed as a script ``python code/setup_directories.py`` we
    # simply run the creation routine.  Any exception will propagate, which
    # is intentional – the calling process (e.g. the quickstart run‑book)
    # should fail loudly if the directories cannot be created.
    create_directory_structure()
    print("Directory structure created successfully.")