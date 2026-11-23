"""
create_skeleton.py
------------------

This module provides a simple command‑line utility that creates the
repository skeleton required by the project.  The skeleton consists of the
following top‑level directories:

    src/
    tests/
    data/
    results/
    docs/
    contracts/

The script is deliberately lightweight – it only creates the directories
if they do not already exist and exits with a zero status code.  It is
invoked by the CI integration tests (see ``tests/test_skeleton.py``) to
guarantee that the expected layout is present before any further
processing occurs.
"""

import sys
from pathlib import Path
from typing import Iterable

# The list of directories that constitute the project skeleton.
SKELETON_DIRS: Iterable[Path] = (
    Path("src"),
    Path("tests"),
    Path("data"),
    Path("results"),
    Path("docs"),
    Path("contracts"),
)


def create_directories(base_path: Path = Path.cwd()) -> None:
    """
    Create all skeleton directories under ``base_path`` if they are missing.

    Parameters
    ----------
    base_path: Path
        The directory in which the skeleton should be created.  By default
        the current working directory is used, which matches the behaviour
        expected by the integration tests.
    """
    for directory in SKELETON_DIRS:
        target = base_path / directory
        try:
            target.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            # Propagate a clear error – the CI test will treat any exception
            # as a failure.
            raise RuntimeError(f"Failed to create skeleton directory {target!s}: {exc}") from exc


def main() -> None:
    """
    Entry point used by the test suite and by developers.

    The function creates the repository skeleton and exits with status 0.
    If an unexpected error occurs, the exception is printed and the process
    exits with status 1.
    """
    try:
        create_directories()
    except Exception as exc:  # pragma: no cover – defensive programming
        print(f"Error creating repository skeleton: {exc}", file=sys.stderr)
        sys.exit(1)
    else:
        # Successful creation – silence any output to keep CI logs clean.
        sys.exit(0)


if __name__ == "__main__":
    main()
