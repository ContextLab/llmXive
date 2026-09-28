"""
setup_data_directories.py
-------------------------

This module provides utilities to create the required data directory
hierarchy for the project. It defines a small helper ``ensure_directory``
that creates a directory (including any missing parents) and a ``main``
entry‑point that creates the four top‑level data sub‑folders:

- ``data/stimuli/``
- ``data/processed/``
- ``data/measurements/``
- ``data/raw/``

The script is deliberately simple: it can be executed directly
(``python code/setup_data_directories.py``) or imported by the test suite.
"""

import os
from pathlib import Path
from typing import Union

def ensure_directory(path: Union[str, Path]) -> Path:
    """
    Ensure that the directory ``path`` exists.

    Parameters
    ----------
    path : Union[str, Path]
        The directory to create.

    Returns
    -------
    Path
        The ``Path`` object for the created (or already existing) directory.
    """
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path

def main() -> None:
    """
    Create the required data directories under the project root.
    The function is idempotent – calling it multiple times will not raise
    errors and will leave the directory tree intact.
    """
    project_root = Path.cwd()
    data_root = project_root / "data"

    # List of sub‑directories that must exist under ``data/``
    subdirs = [
        "stimuli",
        "processed",
        "measurements",
        "raw",
    ]

    for sub in subdirs:
        ensure_directory(data_root / sub)

if __name__ == "__main__":
    # When executed as a script, simply run the creation routine.
    main()
