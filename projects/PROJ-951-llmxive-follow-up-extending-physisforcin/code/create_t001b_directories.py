"""
create_t001b_directories.py
---------------------------
This module creates the required subdirectory hierarchy for the
``PROJ-951-llmxive-follow-up-extending-physisforcin`` project under the
``code`` directory.

The expected layout is::

    code/
        src/
            generation/
            filtering/
            training/
            evaluation/
            augmentation/
            utils/
        tests/
            unit/
            integration/
        data/
            raw/
            curated/
            eval/
            validation/

The ``create_t001b_directories`` function is idempotent – it will not raise
an error if a directory already exists.  The ``main`` entry‑point resolves
the project root based on the location of this file and invokes the helper.

This script is used by ``run_t001b.py`` and is also importable from unit
tests.
"""

import os
from pathlib import Path
from typing import List

# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------
def create_t001b_directories(project_root: Path) -> List[Path]:
    """
    Create the sub‑directory structure required for phase 1.

    Parameters
    ----------
    project_root: Path
        Path to the ``code`` directory of the project (i.e. the directory
        that already contains the empty root created by T001a).

    Returns
    -------
    List[Path]
        A list of the directories that were created (or already existed).
    """
    # Define the relative directory tree
    subdirs = [
        # top‑level folders
        Path("src"),
        Path("tests"),
        Path("data"),
        # src sub‑modules
        Path("src/generation"),
        Path("src/filtering"),
        Path("src/training"),
        Path("src/evaluation"),
        Path("src/augmentation"),
        Path("src/utils"),
        # tests sub‑modules
        Path("tests/unit"),
        Path("tests/integration"),
        # data sub‑folders
        Path("data/raw"),
        Path("data/curated"),
        Path("data/eval"),
        Path("data/validation"),
    ]

    created_paths: List[Path] = []
    for rel_path in subdirs:
        full_path = project_root / rel_path
        # ``parents=True`` creates any missing ancestors; ``exist_ok=True`` makes
        # the call idempotent.
        full_path.mkdir(parents=True, exist_ok=True)
        created_paths.append(full_path)

    return created_paths

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Resolve the project root (the directory containing this file's ``code``
    sibling) and create the directory hierarchy.
    """
    # ``create_t001b_directories.py`` lives inside ``code/``; the project root
    # we need is the parent directory of this file.
    project_root = Path(__file__).resolve().parent
    created = create_t001b_directories(project_root)

    # Simple feedback for manual runs – the test suite does not depend on
    # stdout, but it is helpful for developers.
    print("Created/verified the following directories:")
    for p in created:
        print(f"  - {p}")

if __name__ == "__main__":
    main()
