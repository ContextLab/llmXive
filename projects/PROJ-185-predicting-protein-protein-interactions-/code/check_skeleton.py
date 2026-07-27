"""Utility to verify that the repository skeleton directories exist.

The function ``missing_directories`` returns a list of any expected
top‑level directories that are absent.  The ``main`` function exits with
status code ``0`` when everything is present and ``1`` otherwise,
printing a helpful message.  This script is intended for CI usage (e.g.,
as a step that fails the build if the skeleton is incomplete) and is also
exercised by the unit tests in ``tests/test_skeleton_directories.py``.
"""

import sys
from pathlib import Path
from typing import List


# The same list used by ``create_skeleton`` – keeping them in sync avoids
# accidental mismatches.
EXPECTED_DIRS = [
    "src",
    "tests",
    "data",
    "results",
    "docs",
    "contracts",
]


def _project_root() -> Path:
    """
    Resolve the repository root directory.

    This file lives in ``code/``; the root is its parent directory.
    """
    return Path(__file__).resolve().parent.parent


def missing_directories(root: Path = None) -> List[Path]:
    """
    Return a list of expected skeleton directories that are missing.

    Parameters
    ----------
    root : Path, optional
        The directory to treat as the repository root.  If omitted, the
        function determines the root relative to this file.

    Returns
    -------
    List[Path]
        Paths (relative to ``root``) of directories that do not exist.
    """
    if root is None:
        root = _project_root()
    missing = []
    for rel in EXPECTED_DIRS:
        if not (root / rel).is_dir():
            missing.append(root / rel)
    return missing


def main(argv: list = None) -> None:
    """
    CLI entry point used by CI scripts.

    Exits with ``0`` if all skeleton directories are present, otherwise
    prints the missing paths and exits with ``1``.
    """
    if argv is None:
        argv = sys.argv[1:]  # noqa: F841  (reserved for future flags)

    root = _project_root()
    missing = missing_directories(root)

    if missing:
        print("Missing required repository directories:", file=sys.stderr)
        for p in missing:
            print(f"  - {p}", file=sys.stderr)
        sys.exit(1)
    else:
        # Successful verification – print nothing (or a brief confirmation
        # for interactive runs).
        print("All repository skeleton directories are present.")
        sys.exit(0)


if __name__ == "__main__":
    main()