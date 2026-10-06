import os
from pathlib import Path
from typing import Optional, List, Dict, Any

# Project root is assumed to be the directory containing 'code/'
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Paths
DATA_RAW_PATH = _PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_PATH = _PROJECT_ROOT / "data" / "processed"
LOG_PATH = _PROJECT_ROOT / "logs"
RESULTS_PATH = _PROJECT_ROOT / "results"
DOCS_PATH = _PROJECT_ROOT / "docs"

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_MAX_BYTES = int(os.getenv("LOG_MAX_BYTES", 10 * 1024 * 1024))  # 10MB
LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", 5))


def get_project_root() -> Path:
    """
    Return the absolute path to the project root.

    Returns:
        Path object pointing to the project root.
    """
    return _PROJECT_ROOT


def get_data_path() -> Path:
    """
    Return the path to the data directory.

    Returns:
        Path object pointing to the data directory.
    """
    return _PROJECT_ROOT / "data"


def get_results_path() -> Path:
    """
    Return the path to the results directory.

    Returns:
        Path object pointing to the results directory.
    """
    return RESULTS_PATH


def get_log_path() -> Path:
    """
    Return the path to the logs directory.

    Returns:
        Path object pointing to the logs directory.
    """
    return LOG_PATH
