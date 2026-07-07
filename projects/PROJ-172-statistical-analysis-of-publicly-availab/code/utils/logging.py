"""
Logging and error handling infrastructure for the llmXive sports prediction pipeline.

This module provides:
- Centralized logging configuration (console + file)
- Structured loggers for different pipeline stages
- Error handling wrappers that log exceptions and re-raise
- Integration with artifact hashing for audit trails
"""
import logging
import sys
import os
import traceback
from pathlib import Path
from typing import Optional, Any, Dict
from datetime import datetime

# Import checksum utilities from sibling module
try:
    from checksum_manifest import compute_file_checksum
except ImportError:
    # Fallback for direct execution or different import context
    compute_file_checksum = None


# Default log format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Global logger registry
_loggers: Dict[str, logging.Logger] = {}
_initialized = False


def _get_project_root() -> Path:
    """Determine the project root directory."""
    # Assume code/utils/ is two levels deep from root
    return Path(__file__).resolve().parent.parent.parent


def setup_logging(
    log_level: int = logging.INFO,
    log_file: Optional[str] = None,
    enable_console: bool = True
) -> None:
    """
    Configure the root logging infrastructure.

    Args:
        log_level: Minimum log level (e.g., logging.DEBUG, logging.INFO)
        log_file: Optional path to a log file. If None, only console output.
        enable_console: Whether to log to stdout/stderr.
    """
    global _initialized

    if _initialized:
        return

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Formatter
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # File handler
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    _initialized = True
    logging.getLogger(__name__).info("Logging infrastructure initialized.")


def get_logger(name: str) -> logging.Logger:
    """
    Get a named logger, creating it if necessary.

    Args:
        name: Logger name (usually __name__ of the calling module).

    Returns:
        Configured logger instance.
    """
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)
    if not logger.handlers:
        # Inherit handlers from root
        logger.setLevel(logging.DEBUG)
        logger.propagate = True

    _loggers[name] = logger
    return logger


def log_info(logger: logging.Logger, message: str, **kwargs: Any) -> None:
    """Log an informational message."""
    logger.info(message, extra=kwargs)


def log_warning(logger: logging.Logger, message: str, **kwargs: Any) -> None:
    """Log a warning message."""
    logger.warning(message, extra=kwargs)


def log_error(logger: logging.Logger, message: str, **kwargs: Any) -> None:
    """Log an error message."""
    logger.error(message, extra=kwargs)


def log_debug(logger: logging.Logger, message: str, **kwargs: Any) -> None:
    """Log a debug message."""
    logger.debug(message, extra=kwargs)


def log_exception(logger: logging.Logger, message: str, exc: Optional[Exception] = None) -> None:
    """
    Log an exception with full traceback.

    Args:
        logger: Logger instance.
        message: Contextual message.
        exc: Optional exception instance. If None, uses current exception.
    """
    if exc:
        logger.exception(f"{message}: {exc}")
    else:
        logger.exception(message)


def log_artifact_hash(
    logger: logging.Logger,
    artifact_path: str,
    artifact_name: str,
    description: str = ""
) -> Optional[str]:
    """
    Compute and log the SHA-256 hash of an artifact for audit trails.

    Args:
        logger: Logger instance.
        artifact_path: Path to the artifact file.
        artifact_name: Human-readable name for the artifact.
        description: Optional description of the artifact.

    Returns:
        The hex digest of the checksum, or None if computation failed.
    """
    if compute_file_checksum is None:
        logger.warning(f"Checksum computation unavailable for {artifact_name}")
        return None

    try:
        checksum = compute_file_checksum(artifact_path)
        msg = f"Artifact Hash: {artifact_name} -> {checksum}"
        if description:
            msg += f" ({description})"
        logger.info(msg)
        return checksum
    except FileNotFoundError:
        logger.error(f"Artifact not found for hash: {artifact_path}")
        return None
    except Exception as e:
        logger.error(f"Failed to compute hash for {artifact_name}: {e}")
        return None


def handle_error(
    logger: logging.Logger,
    error_message: str,
    exception: Optional[Exception] = None,
    should_raise: bool = True
) -> None:
    """
    Centralized error handling wrapper.

    Logs the error, optionally logs the traceback, and re-raises if requested.

    Args:
        logger: Logger instance.
        error_message: Contextual error message.
        exception: The exception instance (if known).
        should_raise: If True, re-raises the exception after logging.
    """
    if exception:
        log_exception(logger, error_message, exception)
    else:
        logger.error(error_message)

    if should_raise:
        if exception:
            raise exception
        else:
            raise RuntimeError(error_message)


# Convenience function for pipeline entry points
def pipeline_entry(logger_name: str = "pipeline") -> logging.Logger:
    """
    Get a logger configured for pipeline execution.

    Args:
        logger_name: Name for the logger.

    Returns:
        Logger instance.
    """
    logger = get_logger(logger_name)
    logger.info(f"Pipeline started: {logger_name}")
    return logger