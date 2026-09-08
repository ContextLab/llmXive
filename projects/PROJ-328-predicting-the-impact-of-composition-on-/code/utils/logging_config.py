"""
Logging configuration utilities.
"""
import logging
import sys
import os
from pathlib import Path
from typing import Optional

from utils.error_handlers import ConfigurationError

# Ensure project root is in path
project_root = Path(__file__).resolve().parent.parent.parent
logs_dir = project_root / "logs"
logs_dir.mkdir(exist_ok=True)

_logger_instance: Optional[logging.Logger] = None


def setup_logging(log_file: Optional[str] = None, level: int = logging.INFO) -> None:
    """
    Set up logging configuration.

    Args:
        log_file: Optional path to log file. If None, logs to console only.
        level: Logging level (e.g., logging.INFO, logging.DEBUG).
    """
    if _logger_instance is not None:
        return  # Already configured

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(console_format)
    root_logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(level)
        file_format = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_format)
        root_logger.addHandler(file_handler)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Logger name (module name).

    Returns:
        Configured logger instance.
    """
    if _logger_instance is None:
        setup_logging()

    logger_name = name if name else "solder_pipeline"
    return logging.getLogger(logger_name)


def init_project_logger(log_file: Optional[str] = None) -> logging.Logger:
    """
    Initialize the project logger with a specific log file.

    Args:
        log_file: Path to the log file.

    Returns:
        Configured logger instance.
    """
    global _logger_instance
    if _logger_instance is None:
        if log_file is None:
            log_file = str(project_root / "logs" / "pipeline.log")
        setup_logging(log_file=log_file)
        _logger_instance = logging.getLogger("solder_pipeline")
    return _logger_instance
