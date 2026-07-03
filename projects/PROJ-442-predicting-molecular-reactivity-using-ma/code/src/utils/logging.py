"""
Centralized logging setup for the llmXive molecular reactivity project.

Configures a unified logging handler that writes to both console and file,
with rotation based on size to prevent disk exhaustion during long runs.
"""
import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Project root relative to this file (assuming code/src/utils/)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_LOG_DIR = _PROJECT_ROOT / "logs"
_LOG_FILE = _LOG_DIR / "pipeline.log"

# Ensure log directory exists
_LOG_DIR.mkdir(parents=True, exist_ok=True)

# Default configuration
_DEFAULT_LEVEL = logging.INFO
_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
_BACKUP_COUNT = 5


def setup_logger(
    name: str,
    level: int = _DEFAULT_LEVEL,
    log_file: Path | None = None,
    console: bool = True,
) -> logging.Logger:
    """
    Configure and return a logger with file and console handlers.
    
    Args:
        name: Logger name (usually __name__).
        level: Minimum log level.
        log_file: Optional path to log file. Defaults to project logs/pipeline.log.
        console: If True, add a StreamHandler for stdout.
    
    Returns:
        Configured logging.Logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid adding duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    formatter = logging.Formatter(_LOG_FORMAT)

    # File Handler (Rotating)
    file_path = log_file if log_file else _LOG_FILE
    try:
        file_handler = RotatingFileHandler(
            file_path, maxBytes=_MAX_BYTES, backupCount=_BACKUP_COUNT, encoding="utf-8"
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        # Fallback to stderr if file logging fails
        sys.stderr.write(f"Warning: Could not initialize file logging: {e}\n")

    # Console Handler
    if console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger


def get_logger(name: str = "molecular_reactivity") -> logging.Logger:
    """
    Retrieve the project's main logger instance.
    
    Args:
        name: Optional sub-logger name.
    
    Returns:
        Configured logging.Logger.
    """
    return setup_logger(name)


# Convenience instance for immediate use
logger = get_logger()
