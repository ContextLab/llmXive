"""
Helper utilities that expose the project's data directories.
The functions return ``Path`` objects rooted at the repository's top‑level
``paths.root`` (provided by ``llmxive_toolkit``).  They are deliberately tiny
to avoid circular imports and to keep the public API stable for the other
modules.
"""
from pathlib import Path
from llmxive_toolkit import paths


def get_raw_path() -> Path:
    """
    Return the absolute path to ``data/raw``.

    The rest of the codebase expects a concrete ``Path`` object, not a
    string, so we keep the return type explicit.
    """
    return paths.data("raw")


def get_processed_path() -> Path:
    """
    Return the absolute path to ``data/processed``.
    """
    return paths.data("processed")


def get_results_path() -> Path:
    """
    Return the absolute path to ``data/results``.
    """
    return paths.data("results")


def ensure_dir(p: Path) -> None:
    """
    Convenience wrapper that creates ``p`` and all parent directories if they
    do not already exist.  This mirrors the behaviour of ``paths.<folder>()``
    but works with arbitrary ``Path`` objects.
    """
    p.mkdir(parents=True, exist_ok=True)