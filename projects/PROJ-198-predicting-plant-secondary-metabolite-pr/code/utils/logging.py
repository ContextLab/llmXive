"""
Logging infrastructure for the llmXive plant metabolite prediction pipeline.

Provides a centralized logging setup with both file and console handlers,
supporting different log levels and structured output for debugging and auditing.
"""
import logging
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any

# Import project config to retrieve data paths
# Using the relative import structure expected in the codebase
try:
    from config import get_data_path
except ImportError:
    # Fallback for direct execution or different import context
    def get_data_path() -> Path:
        return Path("data")

# Default log level
DEFAULT_LEVEL = logging.INFO

# Log directory structure
LOG_DIR_NAME = "logs"
LOG_FILE_NAME = "pipeline.log"

# Formatter patterns
CONSOLE_FORMATTER = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

FILE_FORMATTER = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Global logger instance to prevent re-initialization
_logger: Optional[logging.Logger] = None
_initialized: bool = False


def _ensure_log_dir() -> Path:
    """
    Ensures the log directory exists within the project's data/raw or data structure.
    Returns the path to the log directory.
    """
    # Attempt to use the project's configured data path
    try:
        base_path = get_data_path()
    except Exception:
        # Fallback to project root if config fails
        base_path = Path.cwd() / "data"

    log_dir = base_path.parent / LOG_DIR_NAME
    if not log_dir.exists():
        log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def setup_logging(
    level: int = DEFAULT_LEVEL,
    log_file: Optional[str] = None,
    enable_console: bool = True,
    enable_file: bool = True
) -> logging.Logger:
    """
    Configures the root logger for the project with console and file handlers.

    Args:
        level: The logging level (e.g., logging.DEBUG, logging.INFO).
        log_file: Optional custom filename for the log file. Defaults to 'pipeline.log'.
        enable_console: If True, adds a StreamHandler to stdout.
        enable_file: If True, adds a FileHandler to a log file.

    Returns:
        The configured logger instance.
    """
    global _logger, _initialized

    if _initialized:
        return _logger

    # Get the root logger
    _logger = logging.getLogger("llmXive_pipeline")
    _logger.setLevel(level)

    # Clear existing handlers to avoid duplicates on re-calls
    _logger.handlers.clear()

    log_dir = _ensure_log_dir()
    log_path = log_dir / (log_file or LOG_FILE_NAME)

    # Console Handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(CONSOLE_FORMATTER)
        _logger.addHandler(console_handler)

    # File Handler
    if enable_file:
        # Ensure parent directory exists
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path, mode='a', encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(FILE_FORMATTER)
        _logger.addHandler(file_handler)

    # Add a specific handler for errors to stderr if needed, or rely on console
    # Mark as initialized
    _initialized = True

    _logger.info("Logging infrastructure initialized. Log file: %s", log_path)
    return _logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Retrieves a logger instance. Initializes the infrastructure if not already done.

    Args:
        name: Optional name for the child logger (e.g., 'llmXive_pipeline.download').

    Returns:
        A logging.Logger instance.
    """
    if not _initialized:
        setup_logging()

    if name:
        return logging.getLogger(f"llmXive_pipeline.{name}")
    return _logger


# Convenience function to reset logging state (useful for testing)
def reset_logging() -> None:
    """Resets the logging state, clearing handlers and allowing re-initialization."""
    global _logger, _initialized
    if _logger:
        for handler in _logger.handlers[:]:
            handler.close()
            _logger.removeHandler(handler)
    _logger = None
    _initialized = False

# Initialize default logger immediately if imported, or wait for explicit call
# For this utility, we wait for explicit setup_logging() or get_logger() to avoid
# side effects during import unless necessary.
# However, to ensure a default exists if someone just calls get_logger() without setup:
if not _initialized:
    # We do not auto-call setup_logging() here to allow configuration control,
    # but get_logger() will trigger it.
    pass
