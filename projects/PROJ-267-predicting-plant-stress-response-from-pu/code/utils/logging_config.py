import logging
import os
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

from .config import LOG_LEVEL, LOG_PATH, LOG_MAX_BYTES, LOG_BACKUP_COUNT


def setup_logging(
    level: int | None = None,
    log_file: str | None = None,
    console: bool = True,
) -> logging.Logger:
    """
    Configure the project logging infrastructure.

    This function sets up a hierarchical logging configuration that:
    1. Ensures the log directory exists.
    2. Creates a rotating file handler for persistent storage of warnings and errors.
    3. Optionally attaches a console handler for immediate feedback during development.
    4. Configures the root logger and returns a named project logger.

    Args:
        level: Logging level (e.g., logging.INFO, logging.WARNING). Defaults to config.
        log_file: Path to the log file. Defaults to config LOG_PATH.
        console: If True, adds a StreamHandler for stdout/stderr.

    Returns:
        logging.Logger: The configured 'plant_stress_pipeline' logger.

    Example Usage:
        logger = setup_logging()
        logger.warning("Dropped 5 rows due to missing UniProt IDs")
    """
    # Resolve configuration defaults
    effective_level = level if level is not None else LOG_LEVEL
    effective_log_file = log_file if log_file is not None else LOG_PATH

    # Ensure log directory exists
    log_dir = Path(effective_log_file).parent
    if not log_dir.exists():
        os.makedirs(log_dir, exist_ok=True)

    # Get the project logger
    logger_name = "plant_stress_pipeline"
    logger = logging.getLogger(logger_name)
    logger.setLevel(effective_level)

    # Prevent adding handlers multiple times if called repeatedly
    if logger.handlers:
        # If handlers exist, we assume config is already set, but we ensure
        # the level is correct in case it was changed.
        logger.setLevel(effective_level)
        return logger

    # Formatter for consistent output
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File Handler: Rotating to prevent log files from growing indefinitely
    # Captures WARNING and above by default, but respects the effective_level
    file_handler = RotatingFileHandler(
        effective_log_file,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(effective_level)
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    # Console Handler: For immediate visibility during development/execution
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(effective_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # Prevent propagation to the root logger to avoid duplicate console output
    # if the root logger is also configured elsewhere
    logger.propagate = False

    logger.info("Logging infrastructure initialized successfully.")
    return logger


def get_logger(name: str | None = None) -> logging.Logger:
    """
    Retrieve a logger instance.

    Args:
        name: Optional sub-logger name (e.g., 'data_ingestion').
             Defaults to the main project logger if None.

    Returns:
        logging.Logger: The requested logger instance.
    """
    if name:
        return logging.getLogger(f"plant_stress_pipeline.{name}")
    return logging.getLogger("plant_stress_pipeline")


# Convenience function for one-off logging without explicit setup call
# (Assumes setup_logging has been called or uses basicConfig as fallback)
def log_warning(msg: str) -> None:
    """Log a warning message to the configured pipeline log."""
    logger = get_logger()
    if not logger.handlers:
        # Fallback to basicConfig if setup wasn't called yet
        logging.basicConfig(
            filename=LOG_PATH,
            level=logging.WARNING,
            format="%(asctime)s - %(levelname)s - %(message)s",
        )
    get_logger().warning(msg)
