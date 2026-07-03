"""
Logging infrastructure for the llmXive ecotourism regeneration pipeline.

This module configures a centralized logging system that:
1. Writes detailed logs to `data/logs/pipeline.log`
2. Provides a convenient `get_logger()` function for module-specific loggers
3. Ensures log directory existence on first import
4. Configures standard formatting with timestamps and log levels
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional

# Import project configuration to ensure directories exist
# This aligns with the existing API surface in code/config.py
try:
    from config import ensure_directories
except ImportError:
    # Fallback if run as a script without package context
    def ensure_directories():
        """Create necessary directories if they don't exist."""
        dirs = [
            Path("data"),
            Path("data/raw"),
            Path("data/processed"),
            Path("data/ecotourism"),
            Path("data/logs"),
            Path("code/utils"),
            Path("specs/001-ecotourism-regeneration/contracts"),
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

# Default log configuration
LOG_LEVEL = logging.INFO
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_DIR = Path("data/logs")
LOG_FILE = LOG_DIR / "pipeline.log"

_logger_initialized = False

def setup_logging(
    level: int = LOG_LEVEL,
    log_file: Optional[Path] = None,
    console_output: bool = True,
) -> None:
    """
    Configure the root logger for the application.

    Args:
        level: Logging level (e.g., logging.DEBUG, logging.INFO)
        log_file: Path to the log file. Defaults to data/logs/pipeline.log
        console_output: Whether to also output logs to console
    """
    global _logger_initialized

    if _logger_initialized:
        return

    # Ensure log directory exists
    ensure_directories()
    if log_file is None:
        log_file = LOG_FILE
    else:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    # File handler
    try:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    except Exception as e:
        # Fallback to console only if file write fails
        print(f"Warning: Could not create log file {log_file}: {e}", file=sys.stderr)

    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    _logger_initialized = True

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance for a specific module or component.

    Args:
        name: Logger name, typically __name__ of the calling module.
             If None, returns the root logger.

    Returns:
        Configured logging.Logger instance
    """
    # Ensure logging is set up before getting a logger
    setup_logging()

    if name is None:
        return logging.getLogger()
    return logging.getLogger(name)

def get_log_file_path() -> Path:
    """
    Get the current log file path.

    Returns:
        Path object pointing to the active log file
    """
    return LOG_FILE

# Initialize logging on module import for convenience
# This ensures logs are available immediately when other modules import this
setup_logging()

# Convenience logger for this module
logger = get_logger(__name__)

if __name__ == "__main__":
    # Demo/test the logging setup
    test_logger = get_logger("test_module")
    test_logger.debug("This is a debug message")
    test_logger.info("This is an info message")
    test_logger.warning("This is a warning message")
    test_logger.error("This is an error message")
    test_logger.critical("This is a critical message")
    print(f"\nLogs written to: {get_log_file_path()}")