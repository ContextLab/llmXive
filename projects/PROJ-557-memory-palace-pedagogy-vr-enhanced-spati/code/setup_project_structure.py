"""
Project structure creation script.

This script establishes the directory layout required by the implementation
plan:

- data/raw
- data/derived
- code
- tests
- results

For each directory a ``.gitkeep`` file is created so that empty folders are
tracked by Git. The script is safe to run repeatedly; it will not overwrite
existing files.
"""

import os
from pathlib import Path
from typing import List

# ----------------------------------------------------------------------
# Public API – matches the names referenced elsewhere in the repo
# ----------------------------------------------------------------------


def create_directory_structure(base_path: Path = Path(".")) -> List[Path]:
    """
    Create the required top‑level project directories.

    Parameters
    ----------
    base_path : Path, optional
        The directory from which the relative paths are resolved.
        Defaults to the repository root (``"."``).

    Returns
    -------
    List[Path]
        A list of the directories that were (or already were) created.
    """
    # Relative directory names as specified in the task description
    required_dirs = [
        base_path / "data" / "raw",
        base_path / "data" / "derived",
        base_path / "code",
        base_path / "tests",
        base_path / "results",
    ]

    created: List[Path] = []
    for d in required_dirs:
        # ``parents=True`` creates any missing intermediate directories.
        # ``exist_ok=True`` makes the call idempotent.
        d.mkdir(parents=True, exist_ok=True)
        created.append(d.resolve())
    return created


def create_gitkeep_files(directories: List[Path]) -> None:
    """
    Ensure each supplied directory contains a ``.gitkeep`` file.

    The presence of ``.gitkeep`` (an empty file) is a conventional way to
    keep otherwise empty directories under version control.

    Parameters
    ----------
    directories : List[Path]
        List of directories where a ``.gitkeep`` should be placed.
    """
    for d in directories:
        gitkeep_path = d / ".gitkeep"
        if not gitkeep_path.exists():
            # Write an empty file; ``touch`` semantics.
            gitkeep_path.write_text("", encoding="utf-8")


def main() -> None:
    """
    Entry point for the script.

    It creates the directory hierarchy and populates each with a
    ``.gitkeep`` file. Any exception is allowed to propagate so that the CI
    runner fails loudly if something goes wrong (e.g., permission errors).
    """
    # Resolve the repository root (the directory containing this script's
    # parent ``code`` folder) to avoid issues when the script is executed
    # from a different working directory.
    repo_root = Path(__file__).resolve().parent.parent
    dirs = create_directory_structure(base_path=repo_root)
    create_gitkeep_files(dirs)


if __name__ == "__main__":
    # When the module is executed directly, run the main routine.
    main()