"""
Utility functions for accessing common data directory paths within the project.
This module provides a thin wrapper around `llmxive_toolkit.paths` to return
string paths that are used throughout the codebase (e.g., in merge, analysis,
and utils modules). It also supplies a `get_project_root` function that
some legacy imports expect.
"""
from pathlib import Path

from llmxive_toolkit import paths


def get_project_root() -> Path:
    """
    Return the absolute Path object representing the project root directory.
    """
    return paths.root

def ensure_dir(dir_path: str | Path) -> None:
    """
    Ensure that the given directory exists. If ``dir_path`` is a string it
    will be converted to a ``Path`` object.
    """
    path_obj = Path(dir_path)
    path_obj.mkdir(parents=True, exist_ok=True)

def get_processed_path() -> str:
    """
    Return the path to the ``data/processed`` directory as a string.
    """
    return str(paths.data("processed"))

def get_raw_path() -> str:
    """
    Return the path to the ``data/raw`` directory as a string.
    """
    return str(paths.data("raw"))

def get_results_path() -> str:
    """
    Return the path to the ``data/results`` directory as a string.
    """
    return str(paths.data("results"))
