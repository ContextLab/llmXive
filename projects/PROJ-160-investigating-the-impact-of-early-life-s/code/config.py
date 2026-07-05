"""
Configuration module for project paths and constants.

This module defines global constants and helper functions for
accessing project directories and configuration values.
"""

import os
from pathlib import Path
from typing import Final

# Project Root
PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent.parent

# Directory Constants
CODE_DIR: Final[Path] = PROJECT_ROOT / "code"
DATA_DIR: Final[Path] = PROJECT_ROOT / "data"
DATA_RAW_DIR: Final[Path] = DATA_DIR / "raw"
DATA_PROCESSED_DIR: Final[Path] = DATA_DIR / "processed"
TESTS_DIR: Final[Path] = PROJECT_ROOT / "tests"
CONTRACTS_DIR: Final[Path] = PROJECT_ROOT / "contracts"
FIGURES_DIR: Final[Path] = DATA_DIR / "figures"
LOGS_DIR: Final[Path] = PROJECT_ROOT / "logs"

# Analysis Constants
RANDOM_SEED: Final[int] = 42
VIF_THRESHOLD: Final[float] = 5.0
PERMUTATION_COUNT: Final[int] = 5000
MAX_WORKERS: Final[int] = 2
ALPHA_THRESHOLDS: Final[list] = [0.01, 0.05, 0.1]

# ABCD Release Version
ABCD_RELEASE: Final[str] = "4.0"


def get_project_root() -> Path:
    """
    Get the project root directory.

    Returns:
        Path to the project root.
    """
    return PROJECT_ROOT


def get_code_dir() -> Path:
    """
    Get the code directory.

    Returns:
        Path to the code directory.
    """
    return CODE_DIR


def get_data_dir() -> Path:
    """
    Get the data directory.

    Returns:
        Path to the data directory.
    """
    return DATA_DIR


def get_raw_dir() -> Path:
    """
    Get the raw data directory.

    Returns:
        Path to the raw data directory.
    """
    return DATA_RAW_DIR


def get_processed_dir() -> Path:
    """
    Get the processed data directory.

    Returns:
        Path to the processed data directory.
    """
    return DATA_PROCESSED_DIR


def get_figures_dir() -> Path:
    """
    Get the figures directory.

    Returns:
        Path to the figures directory.
    """
    return FIGURES_DIR


def get_logs_dir() -> Path:
    """
    Get the logs directory.

    Returns:
        Path to the logs directory.
    """
    return LOGS_DIR


def ensure_directories() -> None:
    """
    Ensure all required directories exist.
    """
    for dir_path in [
        DATA_RAW_DIR,
        DATA_PROCESSED_DIR,
        TESTS_DIR,
        CONTRACTS_DIR,
        FIGURES_DIR,
        LOGS_DIR
    ]:
        dir_path.mkdir(parents=True, exist_ok=True)


def get_project_path(subpath: str) -> Path:
    """
    Get a full project path from a relative subpath.

    Args:
        subpath: Relative path string.

    Returns:
        Full Path object.
    """
    return PROJECT_ROOT / subpath


if __name__ == "__main__":
    print(f"Project Root: {get_project_root()}")
    print(f"Data Raw: {get_raw_dir()}")
    print(f"Data Processed: {get_processed_dir()}")