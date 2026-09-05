"""
Script to create required data directories for the project.

This module provides a `create_data_directories` function that ensures the
following sub‑directories exist under the repository's top‑level ``data`` folder:

- data/raw
- data/processed
- data/results
- data/external

The function is idempotent (it will not raise an error if the directories already exist)
and returns a list of the created ``Path`` objects.

The module also defines a ``main`` entry point so it can be executed directly:
``python -m code.setup_data_dirs`` or ``python code/setup_data_dirs.py``.
"""

import logging
from pathlib import Path
from typing import List

from config import get_config
from code.utils.logger import get_pipeline_logger

# ----------------------------------------------------------------------
# Helper function
# ----------------------------------------------------------------------
def create_data_directories(base_path: Path = Path.cwd() / "data") -> List[Path]:
    """
    Create the standard data sub‑directories required by the project.

    Parameters
    ----------
    base_path : Path, optional
        The root ``data`` directory. Defaults to ``<repo_root>/data``.

    Returns
    -------
    List[Path]
        List of ``Path`` objects pointing to the created (or already existing)
        sub‑directories.
    """
    subdirs = ["raw", "processed", "results", "external"]
    created_paths: List[Path] = []

    for sub in subdirs:
        dir_path = base_path / sub
        dir_path.mkdir(parents=True, exist_ok=True)
        created_paths.append(dir_path)

    return created_paths

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    CLI entry point that creates the data directories and logs the outcome.
    """
    logger = get_pipeline_logger(__name__)

    # Load configuration (may be used in the future; kept for consistency)
    try:
        _ = get_config()
    except Exception as exc:
        logger.warning(f"Could not load config (non‑critical for directory creation): {exc}")

    try:
        created = create_data_directories()
        logger.info("Data directories ensured:")
        for p in created:
            logger.info(f"  - {p}")
    except Exception as e:
        logger.error(f"Failed to create data directories: {e}")
        raise

if __name__ == "__main__":
    main()