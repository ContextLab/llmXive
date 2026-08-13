"""
setup_project_layout.py

Utility script to create the standard project directory layout required by the
llmXive Geometry Extension project.

The layout consists of the following top‑level directories:
  - src/
  - tests/
  - data/
  - results/
  - contracts/

The script can be invoked directly (e.g. ``python -m setup_project_layout``) or
imported and used programmatically via :func:`create_directories`.
"""

import sys
from pathlib import Path
from typing import Iterable, List

def create_directories(dirs: Iterable[Path]) -> List[Path]:
    """
    Ensure each directory in *dirs* exists.

    Parameters
    ----------
    dirs: Iterable[Path]
        An iterable of :class:`~pathlib.Path` objects representing directories
        to create.

    Returns
    -------
    List[Path]
        A list of the directories that now exist (including those that were
        already present).
    """
    created: List[Path] = []
    for d in dirs:
        # Resolve to an absolute path for consistency
        d_path = d.expanduser().resolve()
        d_path.mkdir(parents=True, exist_ok=True)
        created.append(d_path)
    return created

def main(argv: List[str] | None = None) -> int:
    """
    Entry‑point for the script.

    If command‑line arguments are supplied they are interpreted as additional
    directories to create (relative to the current working directory).  When
    called without arguments the standard layout is created.

    Returns
    -------
    int
        Exit status (0 for success, non‑zero for failure).
    """
    if argv is None:
        argv = sys.argv[1:]

    # Base layout directories relative to the repository root (cwd)
    base_dirs = [
        Path("src"),
        Path("tests"),
        Path("data"),
        Path("results"),
        Path("contracts"),
    ]

    # Append any user‑provided paths
    extra_dirs = [Path(p) for p in argv]
    all_dirs = base_dirs + extra_dirs

    try:
        created = create_directories(all_dirs)
        # Simple feedback for manual runs
        for d in created:
            print(f"Created or verified directory: {d}")
        return 0
    except Exception as exc:
        print(f"Error while creating directories: {exc}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())