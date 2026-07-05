# code/utils/logging.py
# Implements structured logging for the pipeline (FR-007, FR-012).
# Provides a singleton logger configuration and helper functions.

import logging
import os
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

# Constants
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LOG_FILE = "data/pipeline.log"
MAX_BYTES = 5 * 1024 * 1024  # 5 MB
BACKUP_COUNT = 3

_logger: Optional[logging.Logger] = None


def setup_logging(
    log_file: Optional[str] = None,
    level: int = DEFAULT_LOG_LEVEL,
    project_root: Optional[Path] = None,
) -> logging.Logger:
    """
    Configure the global logger for the pipeline.

    Args:
        log_file: Relative or absolute path to the log file. Defaults to 'data/pipeline.log'.
        level: Logging level (e.g., logging.DEBUG, logging.INFO).
        project_root: Base path for resolving relative log paths. Defaults to current working directory.

    Returns:
        The configured logger instance.

    Raises:
        ValueError: If the log directory cannot be created.
    """
    global _logger

    if _logger is not None:
        return _logger

    if project_root is None:
        project_root = Path.cwd()

    if log_file is None:
        log_file = DEFAULT_LOG_FILE

    log_path = Path(log_file)
    if not log_path.is_absolute():
        log_path = project_root / log_file

    # Ensure directory exists
    log_dir = log_path.parent
    if not log_dir.exists():
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise ValueError(f"Failed to create log directory {log_dir}: {e}")

    # Create logger
    _logger = logging.getLogger("pipeline")
    _logger.setLevel(level)

    # Prevent duplicate handlers if called multiple times in same process
    if _logger.handlers:
        _logger.handlers.clear()

    # Formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File Handler (Rotating)
    try:
        file_handler = RotatingFileHandler(
            log_path, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT, encoding="utf-8"
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        _logger.addHandler(file_handler)
    except Exception as e:
        # Fallback to stderr if file logging fails
        sys.stderr.write(f"Warning: Failed to initialize file logging to {log_path}: {e}\n")

    # Console Handler (stderr for warnings/errors, stdout for info/debug usually, but keeping simple)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    _logger.addHandler(console_handler)

    _logger.info("Logging initialized. Log file: %s", log_path)
    return _logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Retrieve the global logger or a child logger.

    Args:
        name: Optional suffix for the logger name (e.g., "pipeline.data_loader").
              If None, returns the root "pipeline" logger.

    Returns:
        A configured logger instance.

    Raises:
        RuntimeError: If setup_logging() has not been called yet.
    """
    global _logger
    if _logger is None:
        # Auto-initialize with defaults if not explicitly set up,
        # but log a warning that it's implicit.
        _logger = setup_logging()
        _logger.warning("Logger accessed before explicit setup. Using defaults.")

    if name is None:
        return _logger
    return _logger.getChild(name)


def log_warning_structured(category: str, message: str, details: Optional[dict] = None) -> None:
    """
    Log a structured warning message (FR-012).

    Args:
        category: A short string identifying the warning category (e.g., "DATA_QUALITY").
        message: The human-readable warning message.
        details: Optional dictionary of key-value pairs for structured context.
    """
    logger = get_logger()
    context = f"[{category}]"
    if details:
        # Format details as a simple string representation for the log line
        # In a more complex system, this might be JSON, but standard logging handles strings best.
        detail_str = ", ".join(f"{k}={v}" for k, v in details.items())
        full_msg = f"{context} {message} | {detail_str}"
    else:
        full_msg = f"{context} {message}"

    logger.warning(full_msg)
