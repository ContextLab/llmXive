"""
setup_data_directories.py

This module creates the required data directory hierarchy for the project:
- data/stimuli/
- data/processed/
- data/measurements/
- data/raw/

It provides a small helper ``ensure_directory`` that safely creates a
directory (including any missing parents) and a ``main`` function that is
executed when the module is run as a script.
"""

import os
from pathlib import Path
from typing import Iterable

def ensure_directory(path: Path | str) -> Path:
    """
    Ensure that *path* exists as a directory.

    Parameters
    ----------
    path: Path | str
        The directory path to create.

    Returns
    -------
    Path
        The absolute ``Path`` object for the created (or already existing)
        directory.
    """
    dir_path = Path(path).expanduser().resolve()
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path

def main(directories: Iterable[Path | str] | None = None) -> None:
    """
    Create the standard data directories.

    Parameters
    ----------
    directories: Iterable[Path | str] | None
        Optional custom list of directories to create. If ``None`` the
        default project‑wide data layout is used.
    """
    if directories is None:
        base = Path(__file__).resolve().parents[2] / "data"
        directories = [
            base / "stimuli",
            base / "processed",
            base / "measurements",
            base / "raw",
        ]

    for d in directories:
        created = ensure_directory(d)
        print(f"Created/verified data directory: {created}")

if __name__ == "__main__":
    # When executed directly, create the default data hierarchy.
    main()
