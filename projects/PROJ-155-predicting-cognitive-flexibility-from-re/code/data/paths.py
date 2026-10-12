"""
Helper utilities for locating project directories.

The functions wrap ``llmxive_toolkit.paths`` to provide a stable API
used throughout the code base (e.g. in tests and data‑handling modules).
"""

from pathlib import Path
from llmxive_toolkit import paths


def get_raw_path() -> Path:
    """
    Path to the raw data directory (``data/raw``).

    Returns
    -------
    pathlib.Path
        The absolute path to the raw data folder, created if missing.
    """
    return paths.data("raw")


def get_processed_path() -> Path:
    """
    Path to the processed data directory (``data/processed``).

    Returns
    -------
    pathlib.Path
        The absolute path to the processed data folder, created if missing.
    """
    return paths.data("processed")


def get_results_path() -> Path:
    """
    Path to the results directory (``data/results``).

    Returns
    -------
    pathlib.Path
        The absolute path to the results folder, created if missing.
    """
    return paths.data("results")


def ensure_dir(p: Path) -> Path:
    """
    Ensure that the directory for *p* exists.

    Parameters
    ----------
    p : pathlib.Path
        Path to a file or directory.  If the path points to a file,
        the parent directory is created.

    Returns
    -------
    pathlib.Path
        The original path (for convenient chaining).
    """
    if p.suffix:  # it's a file path
        p = p.parent
    p.mkdir(parents=True, exist_ok=True)
    return p
