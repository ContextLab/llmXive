"""
Utility helpers for logging, error handling, and path resolution.
"""
import logging
import sys
import os
from pathlib import Path
from typing import Optional, Union

# Project root is the parent of the 'code' directory
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Configure logging
def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[Union[str, Path]] = None,
    name: str = "llsxive"
) -> logging.Logger:
    """
    Configure the root logger for the project.

    Args:
        level: Logging level (e.g., logging.DEBUG, logging.INFO).
        log_file: Optional path to a log file. If provided, logs are written to file.
        name: Name of the logger (default: "lmlxive").

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)
    logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        log_path = Path(log_file)
        # Ensure directory exists
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        logger.addHandler(file_handler)

    return logger


def get_project_root() -> Path:
    """
    Return the absolute path to the project root directory.

    Returns:
        Path object pointing to the project root.
    """
    return _PROJECT_ROOT


def get_data_dir(subdir: Optional[str] = None) -> Path:
    """
    Return the path to the data directory, optionally appending a subdirectory.

    Args:
        subdir: Optional relative subdirectory path (e.g., 'raw', 'processed').

    Returns:
        Path object pointing to the data directory.
    """
    data_dir = _PROJECT_ROOT / "data"
    if subdir:
        data_dir = data_dir / subdir
    return data_dir


def get_code_dir(subdir: Optional[str] = None) -> Path:
    """
    Return the path to the code directory, optionally appending a subdirectory.

    Args:
        subdir: Optional relative subdirectory path.

    Returns:
        Path object pointing to the code directory.
    """
    code_dir = _PROJECT_ROOT / "code"
    if subdir:
        code_dir = code_dir / subdir
    return code_dir


def get_tests_dir(subdir: Optional[str] = None) -> Path:
    """
    Return the path to the tests directory, optionally appending a subdirectory.

    Args:
        subdir: Optional relative subdirectory path.

    Returns:
        Path object pointing to the tests directory.
    """
    tests_dir = _PROJECT_ROOT / "tests"
    if subdir:
        tests_dir = tests_dir / subdir
    return tests_dir


def ensure_dir(path: Union[str, Path]) -> Path:
    """
    Ensure that a directory exists. If it doesn't, create it (including parents).

    Args:
        path: Path to the directory.

    Returns:
        The validated/created Path object.

    Raises:
        OSError: If the directory cannot be created.
    """
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


class ProjectError(Exception):
    """Base exception for project-specific errors."""
    pass


class DataNotFoundError(ProjectError):
    """Raised when required data is not found."""
    pass


class ConfigurationError(ProjectError):
    """Raised when configuration is invalid or missing."""
    pass


class APIError(ProjectError):
    """Raised when an external API call fails."""
    pass