"""Utility script to create the standard data directory structure for the project.

Running this script will ensure that the following sub‑directories exist under the
project's ``data`` folder:

- ``raw``        – for raw downloads and source files
- ``processed``  – for processed datasets, feature matrices, etc.
- ``checkpoints`` – for model checkpoints and intermediate artefacts

The script is idempotent: existing directories are left untouched.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable

def _subdirs(base: Path) -> Iterable[Path]:
    """Yield the full paths of the required sub‑directories."""
    for name in ("raw", "processed", "checkpoints"):
        yield base / name

def create_data_directories(base_path: Path | None = None) -> None:
    """Create the data directory hierarchy.

    Parameters
    ----------
    base_path:
        The root ``data`` directory. If ``None`` (default) the function
        resolves the project root relative to this file and uses the
        ``data`` folder there.

    The function creates the directories ``raw``, ``processed`` and
    ``checkpoints`` under ``base_path``. Missing parent directories are
    created as needed.
    """
    if base_path is None:
        # Resolve ``projects/001-predicting-molecular-dipole-moments/data``.
        # ``setup_data_dirs.py`` lives in ``.../code/``, so ``parents[2]`` is
        # the project root.
        project_root = Path(__file__).resolve().parents[2]
        base_path = project_root / "data"

    for subdir in _subdirs(base_path):
        subdir.mkdir(parents=True, exist_ok=True)

def main(argv: list[str] | None = None) -> int:
    """Entry‑point for ``python -m`` execution."""
    _ = argv  # currently unused – placeholder for future CLI extensions
    create_data_directories()
    print(
        "✅ Data directory structure created at:",
        (Path(__file__).resolve().parents[2] / "data"),
    )
    return 0

if __name__ == "__main__":
    sys.exit(main())