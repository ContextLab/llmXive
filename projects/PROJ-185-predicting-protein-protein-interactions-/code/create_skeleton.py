#!/usr/bin/env python
"""Create the repository skeleton directories for the project.

Running this script will ensure that the standard top‑level directories
`src`, `tests`, `data`, `results`, `docs`, and `contracts` exist.
It also creates minimal placeholder files so that version control
systems track the empty directories.
"""
from pathlib import Path

def main() -> None:
    # The project root is the directory that contains the top‑level
    # folders (src, tests, etc.). This script lives in ``code/``, so we
    # step two levels up to reach the root.
    root = Path(__file__).resolve().parent.parent
    dirs = [
        "src",
        "tests",
        "data",
        "results",
        "docs",
        "contracts",
    ]
    for d in dirs:
        path = root / d
        path.mkdir(parents=True, exist_ok=True)

        # Add a tiny placeholder so the directory is tracked even when empty.
        if d in {"data", "results", "contracts"}:
            placeholder = path / ".gitkeep"
            placeholder.touch(exist_ok=True)
        elif d == "docs":
            readme = path / "README.md"
            if not readme.exists():
                readme.write_text(
                    "# Project Documentation\\n\\n"
                    "This directory contains documentation for the project.\\n"
                )
        else:
            # For Python packages we create an ``__init__.py`` so they are
            # recognised as importable modules.
            init_file = path / "__init__.py"
            init_file.touch(exist_ok=True)

if __name__ == "__main__":
    main()
