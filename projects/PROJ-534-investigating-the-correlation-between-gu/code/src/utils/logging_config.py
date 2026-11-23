"""
Logging configuration module for the gut-microbiome-cognitive-flexibility pipeline.

Configures the root logger to write detailed logs to a file and optionally
to the console. Ensures consistent log formatting across the project.
"""
import logging
import os
from pathlib import Path
from typing import Optional

# Default log directory and file
DEFAULT_LOG_DIR = "logs"
DEFAULT_LOG_FILE = "pipeline.log"
DEFAULT_LOG_LEVEL = logging.INFO

# Log format string
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(
    log_dir: Optional[str] = None,
    log_file: Optional[str] = None,
    log_level: int = DEFAULT_LOG_LEVEL,
    console_output: bool = True,
) -> logging.Logger:
    """
    Configure the root logger for the pipeline.

    Args:
        log_dir: Directory path for log files. Defaults to 'logs' relative to project root.
        log_file: Log filename. Defaults to 'pipeline.log'.
        log_level: Logging level (e.g., logging.DEBUG, logging.INFO).
        console_output: If True, also logs to stdout.

    Returns:
        The configured root logger instance.

    Raises:
        FileNotFoundError: If the log directory cannot be created.
    """
    # Resolve paths
    if log_dir is None:
        # Assume project root is parent of 'code' directory if running from there,
        # or current working directory.
        project_root = Path.cwd()
        # Check if we are in a 'code' subdirectory structure
        if (project_root / "code").exists():
            log_path = project_root / "logs"
        else:
            log_path = project_root / DEFAULT_LOG_DIR
    else:
        log_path = Path(log_dir)

    if log_file is None:
        log_file = DEFAULT_LOG_FILE

    log_file_path = log_path / log_file

    # Ensure log directory exists
    try:
        log_path.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise FileNotFoundError(f"Cannot create log directory {log_path}: {e}")

    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Clear existing handlers to avoid duplicates on re-calls
    logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    # File handler
    try:
        file_handler = logging.FileHandler(log_file_path, mode='a', encoding='utf-8')
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except PermissionError as e:
        raise PermissionError(f"Cannot write to log file {log_file_path}: {e}")

    # Console handler (optional)
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # Log startup info
    logger.info("Logging system initialized.")
    logger.info(f"Log file: {log_file_path}")
    logger.info(f"Log level: {logging.getLevelName(log_level)}")

    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance. If name is provided, returns a child logger.
    Otherwise returns the root logger.

    Args:
        name: Optional name for the logger (e.g., module name).

    Returns:
        A logging.Logger instance.
    """
    if name:
        return logging.getLogger(name)
    return logging.getLogger()


# Initialize logging with default settings when this module is imported
# Note: In production, you might want to call setup_logging explicitly in your main entry point
# to control configuration from command line args or config files.
# For now, we provide a safe initialization that can be called multiple times.
_initialized = False

def initialize_default_logging():
    """One-time initialization of default logging configuration."""
    global _initialized
    if not _initialized:
        setup_logging()
        _initialized = True