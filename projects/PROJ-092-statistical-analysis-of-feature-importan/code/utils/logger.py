"""
Logging setup for the feature importance drift analysis pipeline.
"""
import logging
import sys
from pathlib import Path
from typing import Optional

from .config import get_config


def setup_logger(
    name: str,
    log_file: Optional[Path] = None,
    level: Optional[str] = None
) -> logging.Logger:
    """
    Set up a logger with console and optional file handler.

    Args:
        name: Logger name (usually __name__)
        log_file: Optional path to log file
        level: Optional log level override

    Returns:
        Configured logger instance
    """
    config = get_config()
    log_level = getattr(logging, level or config.log_level, logging.INFO)

    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance (creates if doesn't exist)."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        return setup_logger(name)
    return logger


def main() -> None:
    """Main entry point for logger module (testing)."""
    logger = setup_logger("test_logger", log_file=Path("outputs/test.log"))
    logger.info("Logger initialized successfully")
    logger.debug("Debug message")
    logger.warning("Warning message")
    logger.error("Error message")
