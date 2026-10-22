"""
llmXive Project: Predicting Plant Drought Tolerance from RSA Data
Logging Infrastructure Initialization (JSON‑formatted)
"""

import logging
import sys
import json
from pathlib import Path
from logging.handlers import RotatingFileHandler

# Project root is the parent of the 'code' directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = PROJECT_ROOT / "state"
LOG_FILE = LOG_DIR / "pipeline.log"

# Ensure the state directory exists (the platform owns this folder)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Logging configuration constants
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
MAX_BYTES = 5 * 1024 * 1024  # 5 MB
BACKUP_COUNT = 3
DEFAULT_LEVEL = logging.INFO

# ----------------------------------------------------------------------
# JSON formatter for log records
# ----------------------------------------------------------------------
class JSONFormatter(logging.Formatter):
    """
    Formatter that outputs log records as a single-line JSON string.
    Includes timestamp, logger name, level, message, and optional exception.
    """

    def __init__(self, datefmt: str = DATE_FORMAT):
        super().__init__(datefmt=datefmt)

    def format(self, record: logging.LogRecord) -> str:
        # Base record dictionary
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "logger": record.name,
            "level": record.levelname,
            "message": record.getMessage(),
        }

        # Include exception info if present
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_record, ensure_ascii=False)

# Global logger instance (lazy‑initialized)
_logger = None

def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Returns a configured logger instance for the project.

    The returned logger writes JSON‑formatted entries to
    ``state/pipeline.log`` and also streams to stdout.

    Args:
        name: Name of the logger (e.g., 'llmXive', 'code.download_images')

    Returns:
        A configured ``logging.Logger`` instance.
    """
    global _logger

    # Initialise the root logger on first call
    if _logger is None:
        _logger = logging.getLogger(name)
        _logger.setLevel(DEFAULT_LEVEL)

        # Prevent duplicate handlers if get_logger is called repeatedly
        if not _logger.handlers:
            # Console handler (plain text for readability)
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(DEFAULT_LEVEL)
            console_handler.setFormatter(
                logging.Formatter(
                    fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    datefmt=DATE_FORMAT,
                )
            )
            _logger.addHandler(console_handler)

            # Rotating file handler (JSON formatted)
            try:
                file_handler = RotatingFileHandler(
                    LOG_FILE,
                    maxBytes=MAX_BYTES,
                    backupCount=BACKUP_COUNT,
                    encoding="utf-8",
                )
                file_handler.setLevel(DEFAULT_LEVEL)
                file_handler.setFormatter(JSONFormatter())
                _logger.addHandler(file_handler)
            except Exception as e:
                # If file logging cannot be initialised, fall back to console only
                console_handler.error(f"Failed to initialise file logging: {e}")

    # Return a child logger for the requested module name
    if name != "llmXive":
        return logging.getLogger(name)

    return _logger

def setup_logging(level: int = DEFAULT_LEVEL) -> logging.Logger:
    """
    Re‑initialises the logging infrastructure with a new verbosity level.

    Useful for scripts that want to change the global logging level before
    any other imports occur.

    Args:
        level: Logging level (e.g., ``logging.DEBUG``)

    Returns:
        The root project logger.
    """
    global _logger
    _logger = None  # Force re‑creation with the new level

    # Reset the root logger configuration to avoid handler duplication
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    # Re‑initialise the project logger with the requested level
    return get_logger("llmXive")

# Initialise the default logger on module import so that any import of
# ``code`` automatically creates ``state/pipeline.log``.
get_logger()