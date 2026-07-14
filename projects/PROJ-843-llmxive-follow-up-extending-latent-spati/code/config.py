"""
Configuration module for the llmXive follow‑up project.

Provides directory path getters, a flexible ``ensure_directories`` helper,
and a simple summary function. All getters return :class:`pathlib.Path`
objects to simplify downstream path handling.
"""

import os
from pathlib import Path
from typing import Iterable, Union, List, Optional

# Existing configuration functions (preserved)
def get_project_root() -> Path:
    """
    Return the root directory of the project (the directory containing this file's parent).
    """
    return Path(__file__).resolve().parent.parent

# ----------------------------------------------------------------------
# Base directory definitions (all as Path objects)
# ----------------------------------------------------------------------
_BASE_DIR = Path(__file__).resolve().parent.parent  # project root

RAW_DIR: Path = _BASE_DIR / "data" / "raw"
PROCESSED_DIR: Path = _BASE_DIR / "data" / "processed"
STRATIFIED_DIR: Path = _BASE_DIR / "data" / "stratified"
FEATURES_DIR: Path = _BASE_DIR / "data" / "features"
RESULTS_DIR: Path = _BASE_DIR / "data" / "results"

# ----------------------------------------------------------------------
# Getter helpers – always return ``Path`` objects.
# ----------------------------------------------------------------------
def get_raw_dir() -> Path:
    """Return the path to the raw data directory."""
    return RAW_DIR

def get_processed_dir() -> Path:
    """Return the path to the processed data directory."""
    return PROCESSED_DIR

def get_stratified_dir() -> Path:
    """Return the path to the stratified dataset directory."""
    return STRATIFIED_DIR

def get_features_dir() -> Path:
    """Return the path to the extracted‑features directory."""
    return FEATURES_DIR

def get_results_dir() -> Path:
    """Return the path to the results directory."""
    return RESULTS_DIR

# ----------------------------------------------------------------------
# Flexible ``ensure_directories`` implementation.
#
# Accepts:
#   * no argument – creates the standard project directories,
#   * a single ``Path`` or ``str`` – creates that directory,
#   * an iterable of ``Path``/``str`` – creates each entry.
# ----------------------------------------------------------------------
def ensure_directories(
    targets: Optional[Union[Path, str, Iterable[Union[Path, str]]]] = None
) -> None:
    """
    Ensure that the supplied directory (or directories) exist.

    Parameters
    ----------
    targets : Optional[Union[Path, str, Iterable[Union[Path, str]]]]
        If ``None`` (default), the standard project directories are created.
        If a single path (``Path`` or ``str``), that directory is created.
        If an iterable of paths, each directory in the iterable is created.
    """
    # Resolve the canonical set of directories.
    if targets is None:
        dirs: List[Path] = [
            RAW_DIR,
            PROCESSED_DIR,
            STRATIFIED_DIR,
            FEATURES_DIR,
            RESULTS_DIR,
        ]
    elif isinstance(targets, (str, Path)):
        dirs = [Path(targets)]
    else:
        # Assume an iterable of path‑like objects.
        try:
            dirs = [Path(p) for p in targets]
        except TypeError as exc:
            raise TypeError(
                "ensure_directories expects a Path, str, or an iterable of them"
            ) from exc

    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------
# Simple configuration summary (useful for logging / debugging).
# ----------------------------------------------------------------------
def get_config_summary() -> dict:
    """
    Return a dictionary summarising the most important configuration values.
    """
    return {
        "raw_dir": str(get_raw_dir()),
        "processed_dir": str(get_processed_dir()),
        "stratified_dir": str(get_stratified_dir()),
        "features_dir": str(get_features_dir()),
        "results_dir": str(get_results_dir()),
    }