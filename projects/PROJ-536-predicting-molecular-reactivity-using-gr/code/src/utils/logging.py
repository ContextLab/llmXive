"""
Custom logging infrastructure for the Molecular Reactivity Pipeline.

Provides structured logging with specific handlers for tracking
skipped invalid SMILES entries, ensuring auditability and debuggability.
"""
import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from typing import Optional, Dict, Any

# Constants for log file paths relative to project root
# Assuming standard project structure: code/ is the root for this module
# We will resolve paths relative to the script location or environment
_DEFAULT_LOG_DIR = "logs"
_MAIN_LOG_FILE = os.path.join(_DEFAULT_LOG_DIR, "pipeline.log")
_SMILES_ERROR_LOG_FILE = os.path.join(_DEFAULT_LOG_DIR, "smiles_errors.log")

# Logger names
_MAIN_LOGGER_NAME = "molecular_pipeline"
_SMILES_LOGGER_NAME = "molecular_pipeline.smiles_errors"

# Log levels
DEFAULT_LEVEL = logging.INFO
ERROR_LEVEL = logging.ERROR

# Global logger instances cache to prevent re-initialization
_loggers: Dict[str, logging.Logger] = {}


def _ensure_log_dir(log_dir: str) -> None:
    """Create the log directory if it does not exist."""
    if not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir, exist_ok=True)
        except OSError as e:
            print(f"Warning: Could not create log directory {log_dir}: {e}", file=sys.stderr)


def _get_formatter() -> logging.Formatter:
    """Return a standard formatter with timestamp, level, and message."""
    fmt_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    return logging.Formatter(fmt_str, datefmt="%Y-%m-%d %H:%M:%S")


def _init_main_logger() -> logging.Logger:
    """Initialize the main pipeline logger."""
    logger = logging.getLogger(_MAIN_LOGGER_NAME)
    logger.setLevel(DEFAULT_LEVEL)

    # Prevent adding handlers multiple times if called repeatedly
    if logger.handlers:
        return logger

    _ensure_log_dir(_DEFAULT_LOG_DIR)

    # File handler for general logs
    try:
        fh = RotatingFileHandler(
            _MAIN_LOG_FILE, maxBytes=10 * 1024 * 1024, backupCount=5
        )
        fh.setLevel(DEFAULT_LEVEL)
        fh.setFormatter(_get_formatter())
        logger.addHandler(fh)
    except Exception as e:
        print(f"Warning: Could not create file handler for main log: {e}", file=sys.stderr)

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(DEFAULT_LEVEL)
    ch.setFormatter(_get_formatter())
    logger.addHandler(ch)

    return logger


def _init_smiles_error_logger() -> logging.Logger:
    """Initialize the specific logger for invalid SMILES tracking."""
    logger = logging.getLogger(_SMILES_LOGGER_NAME)
    logger.setLevel(ERROR_LEVEL)

    if logger.handlers:
        return logger

    _ensure_log_dir(_DEFAULT_LOG_DIR)

    # Dedicated file handler for SMILES errors
    # This file will only contain ERROR level messages regarding SMILES
    try:
        fh = RotatingFileHandler(
            _SMILES_ERROR_LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3
        )
        fh.setLevel(ERROR_LEVEL)
        # Custom formatter for error logs to include specific context if needed
        error_fmt = "%(asctime)s - %(levelname)s - %(message)s"
        fh.setFormatter(logging.Formatter(error_fmt, datefmt="%Y-%m-%d %H:%M:%S"))
        logger.addHandler(fh)
    except Exception as e:
        print(f"Warning: Could not create file handler for SMILES error log: {e}", file=sys.stderr)

    # Also log to console for immediate feedback during debugging
    ch = logging.StreamHandler(sys.stderr)
    ch.setLevel(ERROR_LEVEL)
    ch.setFormatter(_get_formatter())
    logger.addHandler(ch)

    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Retrieve or create a logger.

    Args:
        name: Optional name for a child logger. If None, returns the main logger.

    Returns:
        A configured logging.Logger instance.
    """
    if name is None:
        if _MAIN_LOGGER_NAME not in _loggers:
            _loggers[_MAIN_LOGGER_NAME] = _init_main_logger()
        return _loggers[_MAIN_LOGGER_NAME]

    if name not in _loggers:
        # Special case for the SMILES error logger
        if name == _SMILES_LOGGER_NAME:
            _loggers[name] = _init_smiles_error_logger()
        else:
            # Standard child logger inheritance
            parent = get_logger()
            child = logging.getLogger(name)
            child.setLevel(DEFAULT_LEVEL)
            # Child loggers inherit handlers from root if not explicitly set,
            # but we ensure they are configured by getting the parent first.
            # To avoid double logging, we rely on propagation to the main handler
            # or add specific handlers if needed.
            _loggers[name] = child

    return _loggers[name]


def log_invalid_smiles(smiles: str, reason: str, index: Optional[int] = None) -> None:
    """
    Log a skipped invalid SMILES entry to the dedicated error logger.

    This function formats a structured error message containing the SMILES string,
    the reason for rejection, and optionally the index in the dataset.

    Args:
        smiles: The invalid SMILES string.
        reason: The reason why the SMILES was invalid (e.g., "Syntax error", "No atoms").
        index: Optional index of the record in the source data.
    """
    logger = get_logger(_SMILES_LOGGER_NAME)
    if index is not None:
        msg = f"Invalid SMILES at index {index}: '{smiles}' - Reason: {reason}"
    else:
        msg = f"Invalid SMILES: '{smiles}' - Reason: {reason}"
    logger.error(msg)


def log_skipped_reaction(reactants: str, product: str, reason: str, index: Optional[int] = None) -> None:
    """
    Log a skipped reaction record due to parsing failure.

    Args:
        reactants: Reactants SMILES string.
        product: Product SMILES string.
        reason: Reason for skipping.
        index: Optional index.
    """
    logger = get_logger(_SMILES_LOGGER_NAME)
    if index is not None:
        msg = f"Skipped reaction at index {index}: Reactants='{reactants}', Product='{product}' - Reason: {reason}"
    else:
        msg = f"Skipped reaction: Reactants='{reactants}', Product='{product}' - Reason: {reason}"
    logger.error(msg)


def log_message(msg: str, level: int = logging.INFO, logger_name: Optional[str] = None) -> None:
    """
    Generic logging helper.

    Args:
        msg: Log message.
        level: Logging level (e.g., logging.INFO, logging.WARNING).
        logger_name: Name of the logger to use.
    """
    logger = get_logger(logger_name)
    logger.log(level, msg)


# Convenience aliases for common log levels
info = lambda msg, name=None: log_message(msg, logging.INFO, name)
warning = lambda msg, name=None: log_message(msg, logging.WARNING, name)
error = lambda msg, name=None: log_message(msg, logging.ERROR, name)
debug = lambda msg, name=None: log_message(msg, logging.DEBUG, name)
