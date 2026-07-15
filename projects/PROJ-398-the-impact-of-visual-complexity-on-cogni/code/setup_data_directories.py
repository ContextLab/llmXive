"""
setup_data_directories.py

This script creates the required data directory structure for the project:

    data/
        stimuli/
        processed/
        measurements/
        raw/

It is intended to be run as a one‑off setup step and can be safely re‑executed;
existing directories will be left untouched.
"""

import os
from pathlib import Path
from typing import Iterable

# Public API -----------------------------------------------------------------

def ensure_directory(dir_path: str) -> Path:
    """
    Ensure that a directory exists.

    Parameters
    ----------
    dir_path: str
        The directory path to create (relative to the project root).

    Returns
    -------
    pathlib.Path
        The Path object for the created (or already existing) directory.
    """
    path = Path(dir_path).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path

def main() -> None:
    """
    Create the four top‑level data sub‑directories required by the project.
    """
    # Define the required sub‑directories relative to the project root.
    required_dirs: Iterable[str] = (
        "data/stimuli",
        "data/processed",
        "data/measurements",
        "data/raw",
    )

    created: list[Path] = []
    for d in required_dirs:
        created.append(ensure_directory(d))

    # Simple feedback for the user.
    print("Created/verified the following data directories:")
    for p in created:
        print(f" - {p}")

# Entry point ----------------------------------------------------------------

if __name__ == "__main__":
    main()