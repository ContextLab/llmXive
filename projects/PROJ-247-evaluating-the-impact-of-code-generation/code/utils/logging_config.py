"""
Logging configuration utilities for the project.

Provides helper functions to set up loggers with both file and console
handlers, ensuring a consistent logging format across scripts.
"""

import logging
from pathlib import Path
from typing import Optional

LOG_DIR = Path("data/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)


def _configure_logger(
    logger: logging.Logger,
    log_file: Optional[Path] = None,
    level: int = logging.INFO,
) -> logging.Logger:
    """
    Internal helper to attach handlers to a logger.

    Args:
        logger: The logger instance to configure.
        log_file: Optional path to a file where logs should be written.
        level: Logging level (default INFO).

    Returns:
        The configured logger.
    """
    logger.setLevel(level)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Clear any existing handlers to avoid duplicate logs
    logger.handlers = []

    # Console (stream) handler
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(level)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    # File handler, if a path is supplied
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def setup_project_logging(name: str, log_file: str) -> logging.Logger:
    """
    Set up a logger for a specific project component.

    This is used by scripts that want to direct logs to a dedicated file
    (e.g., data_curation.log, matching_pipeline.log).

    Args:
        name: Name of the logger (usually the script or component name).
        log_file: Path to the log file relative to the project root.

    Returns:
        Configured ``logging.Logger`` instance.
    """
    log_path = Path(log_file)
    return _configure_logger(logging.getLogger(name), log_path)


def setup_logging(name: str, log_file: Optional[str] = None) -> logging.Logger:
    """
    Convenience wrapper for quick script setup.

    If ``log_file`` is omitted, a default file under ``data/logs`` named
    ``<name>.log`` is used.

    Args:
        name: Logger name (also used as default filename).
        log_file: Optional explicit log file path.

    Returns:
        Configured ``logging.Logger`` instance.
    """
    if log_file is None:
        log_path = LOG_DIR / f"{name}.log"
    else:
        log_path = Path(log_file)
    return _configure_logger(logging.getLogger(name), log_path)


def get_logger(name: str, log_file: Optional[str] = None) -> logging.Logger:
    """
    Retrieve a logger, creating and configuring it on first use.

    This mirrors the behaviour of ``logging.getLogger`` but ensures that
    the logger has the standard project handlers attached.

    Args:
        name: Logger name.
        log_file: Optional log file path; if omitted, logs go only to the console.

    Returns:
        Configured ``logging.Logger`` instance.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        # If the logger has no handlers yet, configure it now.
        _configure_logger(logger, Path(log_file) if log_file else None)
    return logger
