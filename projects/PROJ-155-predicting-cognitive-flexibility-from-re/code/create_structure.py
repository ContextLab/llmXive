"""
Script to create the required project directory structure for the
``Predicting Cognitive Flexibility`` pipeline. It is idempotent – running it
multiple times will not raise errors if the directories already exist.

Execution of this script satisfies the verification step that expects the
directories ``code/``, ``data/raw/``, ``data/processed/``, ``data/results/``,
``docs/`` and ``tests/`` to be present.
"""

import os
from pathlib import Path

from llmxive_toolkit import paths


def ensure_dir(path: Path) -> None:
    """
    Ensure that *path* exists as a directory.
    """
    path.mkdir(parents=True, exist_ok=True)


def main() -> None:
    # Top‑level project directories
    for folder in ["code", "data/raw", "data/processed", "data/results", "docs", "tests"]:
        ensure_dir(Path(folder))

    # Sub‑folders that ``paths`` helpers rely on
    # (these calls also create the directories if they do not exist)
    paths.code()          # creates ``code/`` if missing
    paths.data("raw")     # creates ``data/raw/``
    paths.data("processed")  # creates ``data/processed/``
    paths.data("results")    # creates ``data/results/``
    paths.docs()          # creates ``docs/``
    paths.tests()         # creates ``tests/``

    print("Project directory structure ensured.")


if __name__ == "__main__":
    main()
