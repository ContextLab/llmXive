import logging
import os
import sys
import resource
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

# Constants
LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "pipeline.log"
MAX_BYTES = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT = 5
FORMAT_STRING = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Ensure log directory exists
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Global logger instance
_logger: Optional[logging.Logger] = None

def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Returns a configured logger instance.
    The logger writes to both stdout and a rotating file handler.
    """
    global _logger
    if _logger is None:
        _logger = logging.getLogger(name)
        _logger.setLevel(logging.DEBUG)
        
        # Prevent adding handlers multiple times if called repeatedly in same process
        if _logger.handlers:
            return _logger

        # Console Handler (stdout)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter(FORMAT_STRING))
        _logger.addHandler(console_handler)

        # Rotating File Handler
        file_handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=MAX_BYTES,
            backupCount=BACKUP_COUNT,
            encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(FORMAT_STRING))
        _logger.addHandler(file_handler)

    return logging.getLogger(name)

def log_mode_switch(mode: str, reason: str) -> None:
    """
    Logs a mode switch event with high visibility.
    Used when the pipeline transitions between Primary, Data Insufficient, or Underpowered.
    """
    logger = get_logger("ModeController")
    logger.warning(f"MODE SWITCH: {mode} | Reason: {reason}")
    # Also log to critical for immediate attention in logs
    logger.critical(f"Pipeline mode set to: {mode}")

def log_resource_usage() -> None:
    """
    Logs current memory and CPU resource usage.
    Uses resource module for Unix-like systems.
    Falls back gracefully on Windows if resource limits aren't applicable in the same way.
    """
    logger = get_logger("ResourceMonitor")
    try:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        maxrss_mb = usage.ru_maxrss / 1024  # Convert KB to MB (on Linux/macOS)
        # Note: On Windows, ru_maxrss is in bytes, so division by 1024**2 would be needed.
        # For cross-platform safety in this specific script context, we assume standard CI env (Linux).
        
        logger.info(f"Resource Usage - Max RSS: {maxrss_mb:.2f} MB, User CPU: {usage.ru_utime:.2f}s, Sys CPU: {usage.ru_stime:.2f}s")
    except AttributeError:
        # resource module might not be fully available or behave differently on some platforms
        logger.debug("Resource monitoring skipped: resource module not fully available.")
    except Exception as e:
        logger.warning(f"Failed to log resource usage: {e}")

def log_warning(message: str) -> None:
    """Convenience wrapper to log a warning."""
    get_logger().warning(message)

def log_info(message: str) -> None:
    """Convenience wrapper to log info."""
    get_logger().info(message)

def log_error(message: str) -> None:
    """Convenience wrapper to log an error."""
    get_logger().error(message)

def log_debug(message: str) -> None:
    """Convenience wrapper to log debug info."""
    get_logger().debug(message)
