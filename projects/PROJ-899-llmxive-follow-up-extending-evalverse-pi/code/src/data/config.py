"""
Data configuration and directory management for the EvalVerse pipeline.
Handles creation and validation of data/raw, data/processed, and cache directories.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional

from src.config import get_project_root, get_data_root, get_state_root, get_reports_root, get_figures_root, get_cache_dir


def get_raw_data_path() -> Path:
    """Return the absolute path to the raw data directory."""
    return get_data_root() / "raw"


def get_processed_data_path() -> Path:
    """Return the absolute path to the processed data directory."""
    return get_data_root() / "processed"


def get_state_path() -> Path:
    """Return the absolute path to the state directory."""
    return get_state_root()


def get_figures_path() -> Path:
    """Return the absolute path to the figures directory."""
    return get_figures_root()


def get_reports_path() -> Path:
    """Return the absolute path to the reports directory."""
    return get_reports_root()


def get_cache_path() -> Path:
    """Return the absolute path to the cache directory."""
    return get_cache_dir()


def ensure_directories() -> Dict[str, Path]:
    """
    Create all necessary data directories if they do not exist.
    Returns a dictionary mapping directory names to their Path objects.
    """
    dirs = {
        "raw": get_raw_data_path(),
        "processed": get_processed_data_path(),
        "state": get_state_path(),
        "figures": get_figures_path(),
        "reports": get_reports_path(),
        "cache": get_cache_path(),
    }

    for name, path in dirs.items():
        path.mkdir(parents=True, exist_ok=True)

    return dirs


def is_data_directory_ready() -> bool:
    """
    Check if the essential data directories (raw, processed) exist and are writable.
    """
    try:
        raw_path = get_raw_data_path()
        proc_path = get_processed_data_path()

        if not raw_path.exists() or not proc_path.exists():
            return False

        # Test write permission by creating a temp file
        test_file = raw_path / ".write_test"
        test_file.touch()
        test_file.unlink()
        return True
    except (OSError, IOError):
        return False


def get_data_directories() -> Dict[str, Path]:
    """
    Get a dictionary of all data-related paths.
    """
    return {
        "root": get_data_root(),
        "raw": get_raw_data_path(),
        "processed": get_processed_data_path(),
        "state": get_state_path(),
        "figures": get_figures_path(),
        "reports": get_reports_path(),
        "cache": get_cache_path(),
    }


def get_data_summary() -> Dict[str, Any]:
    """
    Generate a summary of the current data directory structure status.
    """
    dirs = get_data_directories()
    summary = {}
    for name, path in dirs.items():
        summary[name] = {
            "path": str(path),
            "exists": path.exists(),
            "is_dir": path.is_dir() if path.exists() else False,
        }
    return summary
