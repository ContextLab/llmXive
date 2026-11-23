"""
setup_project_structure.py

Utility script to create the required project directory hierarchy for the
``PROJ-236-exploring-the-influence-of-network-topol`` project.

The implementation follows the specification in ``tasks.md``:
- All listed sub‑directories are created under a given root directory.
- The default root is ``projects/PROJ-236-exploring-the-influence-of-network-topol``.
- The script can be invoked from the command line or imported in tests.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable, Union

# -------------------------------------------------------------------------
# Directory layout required by the implementation plan
# -------------------------------------------------------------------------
REQUIRED_SUBDIRS: Iterable[Path] = [
    Path("code/utils"),
    Path("code/tests/unit"),
    Path("code/tests/integration"),
    Path("data/raw"),
    Path("data/networks"),
    Path("data/transport"),
    Path("data/analysis"),
    Path("plots"),
    Path("state/projects"),
]

def create_directories(root: Union[str, Path]) -> None:
    """
    Create the full set of required sub‑directories under *root*.

    Parameters
    ----------
    root: str or pathlib.Path
        The base directory that will contain the hierarchy defined in
        ``REQUIRED_SUBDIRS``.  The function creates each sub‑directory with
        ``parents=True`` and ``exist_ok=True`` so it is safe to call multiple
        times.

    Raises
    ------
    OSError
        Propagated if the filesystem cannot create a directory.
    """
    root_path = Path(root).expanduser().resolve()
    for sub in REQUIRED_SUBDIRS:
        dir_path = root_path / sub
        dir_path.mkdir(parents=True, exist_ok=True)

def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """
    Parse command‑line arguments.

    The script accepts an optional positional argument specifying the project
    root.  If omitted, it defaults to the canonical project location inside the
    repository.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Create the directory structure required for the "
            "PROJ-236-exploring-the-influence-of-network-topol project."
        )
    )
    default_root = (
        Path.cwd()
        / "projects"
        / "PROJ-236-exploring-the-influence-of-network-topol"
    )
    parser.add_argument(
        "project_root",
        nargs="?",
        default=str(default_root),
        help=(
            "Root directory under which the required sub‑directories will be "
            f"created (default: {default_root})."
        ),
    )
    return parser.parse_args(argv)

def main(argv: list[str] | None = None) -> None:
    """
    Entry point for ``python -m code.setup_project_structure`` or direct script
    execution.

    It parses arguments, creates the directory tree, and prints a short
    confirmation message.
    """
    args = _parse_args(argv)
    try:
        create_directories(args.project_root)
    except Exception as exc:
        print(f"Failed to create project structure: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Project structure created under: {Path(args.project_root).resolve()}")

if __name__ == "__main__":
    main()