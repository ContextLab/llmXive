import logging
import sys
from pathlib import Path
from typing import Optional

from .config import get_project_root


def get_logger(name: str = __name__) -> logging.Logger:
    """Get a logger instance with project-specific configuration.

    Args:
        name: Logger name, typically __name__

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_format)

    # Create file handler
    log_path = get_project_root() / 'logs' / 'project.log'
    log_path.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(file_format)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


def configure_root_logger(level: int = logging.INFO) -> None:
    """Configure the root logger for the entire project.

    Args:
        level: Logging level for the root logger
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    if not root_logger.handlers:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)


def get_log_path() -> Path:
    """Get the path to the project log directory.

    Returns:
        Path to the logs directory
    """
    return get_project_root() / 'logs'


def setup_logging_for_script(script_name: str) -> logging.Logger:
    """Set up logging for a specific script.

    Args:
        script_name: Name of the script (without .py extension)

    Returns:
        Configured logger for the script
    """
    logger = get_logger(script_name)
    logger.debug(f"Logging initialized for {script_name}")
    return logger