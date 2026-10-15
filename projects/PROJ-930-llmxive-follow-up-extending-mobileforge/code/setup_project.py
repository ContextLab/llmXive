"""
setup_project.py
-----------------
Script to bootstrap the project directory structure required for the MobileForge
logic‑distillation study.

This script is invoked via its ``main`` function (or ``python -m setup_project``)
and creates the following hierarchy under the project root:

code/
    data/
        raw/
        processed/
        evaluation/
    models/
    utils/
    tests/
        unit/
        integration/
state/

It also ensures that a placeholder ``requirements.txt`` file exists under
``code/`` so that subsequent tasks (e.g., T002) can populate it with pinned
dependencies.

The implementation is deliberately idempotent: existing directories and files
are left untouched.
"""

import sys
from pathlib import Path

def _project_root() -> Path:
    """
    Return the absolute path to the project root directory.
    The script resides in ``code/``; the project root is its parent.
    """
    return Path(__file__).resolve().parent.parent

def _create_directories(root: Path) -> None:
    """
    Create all required directories for the study.

    Parameters
    ----------
    root: Path
        The project root directory.
    """
    dirs = [
        root / "code" / "data" / "raw",
        root / "code" / "data" / "processed",
        root / "code" / "data" / "evaluation",
        root / "code" / "models",
        root / "code" / "utils",
        root / "code" / "tests" / "unit",
        root / "code" / "tests" / "integration",
        root / "state",
    ]

    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def _ensure_requirements_file(root: Path) -> None:
    """
    Ensure that a ``requirements.txt`` file exists under ``code/``.
    If the file already exists it is left untouched; otherwise an empty
    placeholder file is created.

    Parameters
    ----------
    root: Path
        The project root directory.
    """
    req_path = root / "code" / "requirements.txt"
    req_path.touch(exist_ok=True)

def main() -> None:
    """
    Entry point for the bootstrap script.

    It creates the directory tree and the placeholder ``requirements.txt``.
    """
    root = _project_root()
    _create_directories(root)
    _ensure_requirements_file(root)
    print(f"Project bootstrap completed. Root: {root}", file=sys.stderr)

if __name__ == "__main__":
    main()
