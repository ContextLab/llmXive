"""
setup_project_structure.py
--------------------------

This script creates the required project directory layout for the
llmXive research pipeline. It is used by task T001 to ensure that all
necessary top‑level directories exist before any further processing.

Required directories (all relative to the repository root):
  - src/
  - src/utils/
  - data/raw/
  - data/derived/
  - data/annotations/
  - results/
  - tests/
  - specs/
  - contracts/

The script can be imported and the ``create_directories`` function called
directly, or executed as a module/script. When run, it creates any missing
directories and exits with status code ``0``. Errors raise an exception,
causing a non‑zero exit code.
"""

import sys
from pathlib import Path
from typing import List

def _project_root() -> Path:
    """
    Return the absolute path to the repository root (the directory that
    contains the top‑level ``code`` package).
    """
    # This file lives in <repo_root>/code/setup_project_structure.py
    return Path(__file__).resolve().parent.parent

def _required_directories(root: Path) -> List[Path]:
    """
    Return a list of all directories that must exist for the pipeline.
    """
    return [
        root / "src",
        root / "src" / "utils",
        root / "data" / "raw",
        root / "data" / "derived",
        root / "data" / "annotations",
        root / "results",
        root / "tests",
        root / "specs",
        root / "contracts",
    ]

def create_directories() -> List[Path]:
    """
    Create the required directory layout.

    Returns
    -------
    List[Path]
        The list of directories that were ensured to exist.
    """
    root = _project_root()
    dirs = _required_directories(root)
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    return dirs

def main() -> int:
    """
    Entry point for ``python -m code.setup_project_structure`` or direct
    execution. Creates the directories and prints a short summary.

    Returns
    -------
    int
        Exit code: ``0`` on success, ``1`` on unexpected error.
    """
    try:
        created = create_directories()
        print("Created/verified the following directories:")
        for d in created:
            print(f" - {d}")
        return 0
    except Exception as exc:  # pragma: no cover – unexpected failures are fatal
        print(f"Error while creating project layout: {exc}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
