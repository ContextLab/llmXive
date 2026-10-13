"""
Utility functions for accessing project data directories.

This module provides a small wrapper around ``llmxive_toolkit.paths`` to
expose convenient helpers used throughout the pipeline. All functions
return ``str`` paths (compatible with ``os.path`` utilities) and ensure
that the requested directories exist.
"""

from pathlib import Path
from llmxive_toolkit import paths


def get_project_root() -> Path:
    """
    Return the absolute path to the project root directory.

    The file lives in ``code/data/paths.py``; the project root is two
    levels up (``code/data`` → ``code`` → project root).
    """
    return Path(__file__).resolve().parents[2]


def get_raw_path(*subpaths: str) -> str:
    """
    Path to the raw data directory (``data/raw``) optionally extended with
    additional sub‑paths.

    Example:
        get_raw_path()                     -> "<project>/data/raw"
        get_raw_path("HCP_1200", "sub-001") -> "<project>/data/raw/HCP_1200/sub-001"
    """
    return str(paths.data("raw", *subpaths))


def get_processed_path(*subpaths: str) -> str:
    """
    Path to the processed data directory (``data/processed``) optionally
    extended with additional sub‑paths.
    """
    return str(paths.data("processed", *subpaths))


def get_results_path(*subpaths: str) -> str:
    """
    Path to the results directory (``data/results``) optionally extended
    with additional sub‑paths.
    """
    # ``paths.results`` creates ``data/results`` under the project root.
    return str(paths.results(*subpaths))


def ensure_dir(path: str | Path) -> None:
    """
    Ensure that the directory for *path* exists.

    If ``path`` points to a file, the parent directory is created.
    If it already exists, the function does nothing.
    """
    p = Path(path)
    if not p.is_dir():
        p.mkdir(parents=True, exist_ok=True)
