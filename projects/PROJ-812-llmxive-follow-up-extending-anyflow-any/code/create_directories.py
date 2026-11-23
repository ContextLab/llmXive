"""
create_directories.py

Utility script to create the required project directory hierarchy:

    code/
    data/raw/
    data/processed/
    tests/unit/
    tests/integration/

The script can be imported and the ``create_directories`` function called
programmatically, or executed directly as a module.  When run as a script it
returns an exit code ``0`` on success.

The implementation follows the contract defined in the project’s API
surface (see ``code/create_directories.py`` signature documentation).
"""

import sys
from pathlib import Path
from typing import Optional

def _infer_project_root() -> Path:
    """
    Infer the project root directory based on the location of this file.
    The file lives in ``<project_root>/code/create_directories.py``.
    Two levels up from here points to the repository root.
    """
    return Path(__file__).resolve().parents[2]

def create_directories(base_path: Optional[Path] = None) -> None:
    """
    Create the required directory hierarchy.

    Parameters
    ----------
    base_path : pathlib.Path | None
        Root directory under which the hierarchy will be created.
        If ``None`` (default), the project root is inferred from the
        location of this file (two levels up, i.e. the repository root).
    """
    if base_path is None:
        base_path = _infer_project_root()

    # List of directories to create relative to ``base_path``.
    dirs = [
        base_path / "code",
        base_path / "data" / "raw",
        base_path / "data" / "processed",
        base_path / "tests" / "unit",
        base_path / "tests" / "integration",
    ]

    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def _main() -> int:
    """
    Entry‑point used when the module is executed as a script.
    It creates the directory hierarchy and returns an exit status.
    """
    create_directories()
    return 0

if __name__ == "__main__":
    sys.exit(_main())