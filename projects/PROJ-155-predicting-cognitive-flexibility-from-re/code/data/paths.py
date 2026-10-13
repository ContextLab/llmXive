"""
Helper utilities for constructing project‑relative paths.

The functions mirror the simple path helpers used throughout the
codebase (e.g. ``ensure_dir``, ``get_processed_path``). They delegate
to ``llmxive_toolkit.paths`` which creates the directories on
demand.
"""
from pathlib import Path

from llmxive_toolkit import paths


def ensure_dir(p: Path) -> None:
    """
    Ensure that the directory component of *p* exists.

    Args:
        p: Path object – typically a file path. The parent directory
           will be created if it does not already exist.
    """
    p.parent.mkdir(parents=True, exist_ok=True)

def get_raw_path() -> Path:
    """
    Return the path to the raw data directory (``data/raw``).
    """
    return paths.data("raw")

def get_processed_path() -> Path:
    """
    Return the path to the processed data directory (``data/processed``).
    """
    return paths.data("processed")

def get_results_path() -> Path:
    """
    Return the path to the results directory (``data/results``).
    """
    # ``paths.results`` creates ``data/results`` under the project root.
    return paths.results()

def get_figures_path() -> Path:
    """
    Return the path to the figures directory (``figures``).
    """
    return paths.figures()
