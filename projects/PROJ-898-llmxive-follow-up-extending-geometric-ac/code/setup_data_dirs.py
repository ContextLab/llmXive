#!/usr/bin/env python
"""
Script to create the required data sub‑directories and populate each with a ``.gitkeep`` file.

The directories are:
  - data/raw
  - data/generated
  - data/results

Running this script is idempotent – existing directories and ``.gitkeep`` files are left untouched.
"""
import sys
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)


def ensure_dir_and_gitkeep(dir_path):
    """
    Ensure a directory exists and contains an empty ``.gitkeep`` file.

    Parameters
    ----------
    dir_path : pathlib.Path
        Path to the directory to create.
    """
    # ``paths`` helpers automatically create parent directories when needed.
    dir_path.mkdir(parents=True, exist_ok=True)
    gitkeep_path = dir_path / ".gitkeep"
    gitkeep_path.touch(exist_ok=True)
    log.info(f"Created/ensured {gitkeep_path}")


def main() -> int:
    """Entry point for the script."""
    # Define the three top‑level data sub‑folders.
    subfolders = [
        paths.data("raw"),
        paths.data("generated"),
        paths.data("results")
    ]

    for folder in subfolders:
        ensure_dir_and_gitkeep(folder)

    return 0


if __name__ == "__main__":
    sys.exit(main())
