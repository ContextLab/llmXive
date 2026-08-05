"""
Project layout creation utility.

This module provides a simple API to create the standard directory
structure required by the llmXive Geometry Extension project:

    - src/
    - tests/
    - data/
    - results/
    - contracts/

The script can be executed directly:

    $ python code/setup_project_layout.py

which will create the directories relative to the current working
directory (typically the repository root).  The functions are also
importable for use in test suites or other automation tools.
"""

import sys
from pathlib import Path
from typing import Iterable

def create_directories(dirs: Iterable[Path]) -> None:
    """
    Create each directory in ``dirs`` if it does not already exist.

    Parameters
    ----------
    dirs: Iterable[Path]
        An iterable of :class:`pathlib.Path` objects representing the
        directories to be created.  Parent directories are created as
        needed (``parents=True``) and existing directories are ignored
        (``exist_ok=True``).

    Raises
    ------
    OSError
        Propagates any OS‑level error that occurs while creating a
        directory (e.g., permission issues).
    """
    for d in dirs:
        # Resolve to an absolute path for clarity in logs / debugging.
        absolute_path = d.expanduser().resolve()
        absolute_path.mkdir(parents=True, exist_ok=True)

def main(argv: list[str] | None = None) -> None:
    """
    Entry‑point for the command‑line interface.

    If no arguments are supplied, the function creates the default
    project layout.  An optional list of directory names can be passed
    to customise the layout (useful for testing).

    Parameters
    ----------
    argv: list[str] | None
        Command‑line arguments excluding the script name.  If ``None``,
        ``sys.argv[1:]`` is used.
    """
    if argv is None:
        argv = sys.argv[1:]

    # Default layout as defined in ``plan.md``.
    default_dirs = [
        Path("src"),
        Path("tests"),
        Path("data"),
        Path("results"),
        Path("contracts"),
    ]

    # Allow callers to specify additional or alternative directories.
    dirs_to_create = [Path(p) for p in argv] if argv else default_dirs

    create_directories(dirs_to_create)

if __name__ == "__main__":
    main()