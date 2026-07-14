"""
Logging Utilities for the Microglial Morphology Project.

Provides a centralized logging configuration to ensure consistent
log output across all modules. Handles warnings for missing metadata
as per FR-001 and FR-008.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from code.config import CONFIG, get_project_root


def get_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """
    Get a logger instance with project-specific configuration.

    Args:
        name: Name for the logger (typically __name__).
        level: Optional logging level override.

    Returns:
        Configured logging.Logger instance.
    """
    logger = logging.getLogger(name)

    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    # Default level from config or INFO
    if level is None:
        level = getattr(logging, CONFIG.get('log_level', 'INFO').upper(), logging.INFO)
    logger.setLevel(level)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(console_handler)

    # Prevent propagation to root logger to avoid duplicate logs
    logger.propagate = False

    return logger


def setup_file_logging(log_file: Optional[Path] = None, level: Optional[int] = None) -> None:
    """
    Setup file logging for the project.

    Args:
        log_file: Path to the log file. Defaults to project logs directory.
        level: Optional logging level override.
    """
    if log_file is None:
        log_dir = get_project_root() / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / 'pipeline.log'
    else:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger()

    # Avoid adding handlers multiple times
    if any(isinstance(h, logging.FileHandler) for h in logger.handlers):
        return

    # Default level from config or INFO
    if level is None:
        level = getattr(logging, CONFIG.get('log_level', 'INFO').upper(), logging.INFO)

    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)

    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)


def warn_missing_metadata(field: str, file_path: str) -> None:
    """
    Log a standardized warning for missing metadata fields.

    FR-008: Ensure missing metadata is logged as a warning, not an error,
    to allow pipeline continuation.

    Args:
        field: Name of the missing metadata field.
        file_path: Path to the file with missing metadata.
    """
    logger = get_logger(__name__)
    logger.warning(f"Missing metadata field '{field}' for file: {file_path}")
