"""
Project layout creation utility.

This module defines the required directory structure for the
``PROJ-370-evaluating-the-impact-of-code-generation`` project and
provides a ``create_directories`` function that creates those
directories on demand.

The function is used by the unit test ``tests/unit/test_setup_project_structure.py``,
which patches the private ``_REQUIRED_DIRS`` constant to a temporary
list of paths.  The implementation therefore respects the current
value of ``_REQUIRED_DIRS`` (whether the default list or a patched
one) and creates each directory if it does not already exist.

The default layout matches the specification in ``tasks.md`` and
includes the required ``specs/001-evaluating-the-impact-of-code-generation/contracts``
directory (note the exact name required by the task).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Optional

# ----------------------------------------------------------------------
# Helper to locate the repository root (the directory that contains the
# top‑level ``code`` folder).  This file lives at
# <repo_root>/code/setup_project_structure.py.
# ----------------------------------------------------------------------
def _project_root() -> Path:
    """
    Return the absolute path to the repository root.

    The repository root is assumed to be the parent of the ``code``
    directory that contains this file.
    """
    # ``__file__`` -> <repo_root>/code/setup_project_structure.py
    # parents[0] = this file, parents[1] = ``code`` directory,
    # parents[2] = repository root.
    return Path(__file__).resolve().parents[2]

# ----------------------------------------------------------------------
# Default required directories (as Path objects).  The list mirrors the
# layout described in ``tasks.md``.
# ----------------------------------------------------------------------
_REQUIRED_DIRS: List[Path] = [
    # Source code packages
    _project_root() / "code" / "src" / "config",
    _project_root() / "code" / "src" / "extraction",
    _project_root() / "code" / "src" / "detection",
    _project_root() / "code" / "src" / "inference",
    _project_root() / "code" / "src" / "analysis",
    _project_root() / "code" / "src" / "reporting",
    _project_root() / "code" / "src" / "pipeline",
    _project_root() / "code" / "src" / "cli",
    # Test packages
    _project_root() / "code" / "tests" / "unit",
    _project_root() / "code" / "tests" / "integration",
    _project_root() / "code" / "tests" / "contract",
    # Data sub‑folders
    _project_root() / "code" / "data" / "raw",
    _project_root() / "code" / "data" / "annotations",
    _project_root() / "code" / "data" / "derived",
    _project_root() / "code" / "data" / "results",
    # Logs
    _project_root() / "code" / "logs",
    # Specification contracts (exact name required by the task)
    _project_root() / "specs" / "001-eval-llm-review-quality" / "contracts",
]

# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------
def create_directories(extra_paths: Optional[List[Path]] = None) -> List[Path]:
    """
    Ensure that all required directories (and any ``extra_paths``) exist.

    Parameters
    ----------
    extra_paths : list of pathlib.Path, optional
        Additional directories that callers may want to guarantee exist.
        If a path points to a file, its parent directory is created.

    Returns
    -------
    list of pathlib.Path
        The absolute paths of all directories that now exist.
    """
    # Resolve the list of directories we need to create.
    dirs_to_create: List[Path] = list(_REQUIRED_DIRS)  # copy default list
    if extra_paths:
        # Convert any file paths to their parent directories.
        for p in extra_paths:
            dir_path = p if p.is_dir() else p.parent
            dirs_to_create.append(dir_path)

    created: List[Path] = []
    for d in dirs_to_create:
        # ``mkdir`` with ``parents=True`` creates intermediate directories
        # and ``exist_ok=True`` makes the operation idempotent.
        d.mkdir(parents=True, exist_ok=True)
        created.append(d.resolve())

    return created

# ----------------------------------------------------------------------
# Convenience entry point used by ``python -m code.setup_project_structure``.
# ----------------------------------------------------------------------
def main() -> int:
    """
    CLI entry point: create the required layout and exit with status 0
    on success, or 1 on unexpected error.
    """
    try:
        create_directories()
        print("Project directory layout created successfully.")
        return 0
    except Exception as exc:  # pragma: no cover – defensive
        print(f"Error creating project layout: {exc}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())