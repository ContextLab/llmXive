"""
Utility functions for accessing project data directories.

This module provides a thin wrapper around ``llmxive_toolkit.paths`` to
expose the directory paths used throughout the codebase. It also offers
a simple ``ensure_dir`` helper that creates a directory (including any
missing parents) for a given path.

The functions return string paths because the existing codebase mixes
``str`` and ``pathlib.Path`` usage. Returning ``str`` keeps backward
compatibility while still leveraging the robust path handling of
``llmxive_toolkit.paths``.
"""

from pathlib import Path
from llmxive_toolkit import paths


def get_project_root() -> str:
    """
    Return the absolute path to the project root directory.

    The original ``code.data.__init__`` expected this symbol, so we
    provide it here to satisfy the import.
    """
    return str(paths.root)


def get_raw_path() -> str:
    """
    Path to the raw HCP (or simulated) data directory.

    Returns:
        str: ``<project>/data/raw/HCP_1200``
    """
    raw_path = paths.data("raw", "HCP_1200")
    raw_path.mkdir(parents=True, exist_ok=True)
    return str(raw_path)


def get_processed_path() -> str:
    """
    Path to the processed data directory.

    Returns:
        str: ``<project>/data/processed``
    """
    proc_path = paths.data("processed")
    proc_path.mkdir(parents=True, exist_ok=True)
    return str(proc_path)


def get_results_path() -> str:
    """
    Path to the results directory (used for JSON summaries, etc.).

    Returns:
        str: ``<project>/data/results``
    """
    res_path = paths.data("results")
    res_path.mkdir(parents=True, exist_ok=True)
    return str(res_path)


def ensure_dir(p: Path | str) -> None:
    """
    Ensure that the directory ``p`` exists.

    Args:
        p: Path or string representing a directory.
    """
    Path(p).mkdir(parents=True, exist_ok=True)


__all__ = [
    "get_project_root",
    "get_raw_path",
    "get_processed_path",
    "get_results_path",
    "ensure_dir",
]