import logging
import os
from pathlib import Path

def setup_logger(name: str = "dssc_research", level: int = logging.INFO) -> logging.Logger:
    """
    Configure and return a logger that writes to both:
    1. A file at `code/logs/app.log`
    2. stdout (console)

    The logger uses the provided name and level. It ensures the log directory
    exists before attempting to write.

    Args:
        name: The name of the logger instance.
        level: The logging level (default: INFO).

    Returns:
        A configured logging.Logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Prevent adding handlers multiple times if called repeatedly
    if logger.handlers:
        return logger

    # Ensure the log directory exists
    log_dir = Path("code/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "app.log"

    # Create formatters
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_formatter = logging.Formatter(
        "%(levelname)s: %(message)s"
    )

    # File Handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)
    file_handler.setFormatter(file_formatter)

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(console_formatter)

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
