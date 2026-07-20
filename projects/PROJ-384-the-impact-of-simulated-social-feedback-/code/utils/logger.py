import logging
import os
from pathlib import Path

from .config import LOGS_DIR, LOG_FILE_NAME


def setup_logger(name: str = "pipeline", level: int = logging.INFO) -> logging.Logger:
    """
    Set up a logger with both file and console handlers.

    Ensures the logs directory exists and attaches:
      - A FileHandler writing to `logs/pipeline.log`
      - A StreamHandler writing to stdout with a concise format

    Args:
        name: Logger name (usually __name__ of the caller)
        level: Logging level (default: INFO)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Prevent adding handlers multiple times if this function is called repeatedly
    if logger.handlers:
        return logger

    # Ensure logs directory exists
    logs_path = Path(LOGS_DIR)
    logs_path.mkdir(parents=True, exist_ok=True)

    log_file_path = logs_path / LOG_FILE_NAME

    # File handler
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setLevel(level)
    file_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_format)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_format = logging.Formatter(
        "%(levelname)s: %(message)s"
    )
    console_handler.setFormatter(console_format)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


# Convenience instance for direct imports if needed
pipeline_logger = setup_logger("pipeline")
