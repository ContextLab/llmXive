"""
Logging infrastructure configuration for llmXive research pipeline.

Provides structured logging output to both console and file handlers.
Ensures consistent log formatting across all analysis modules.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional

# Project root relative to this file (code/analysis -> root)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Ensure logs directory exists
_LOGS_DIR = _PROJECT_ROOT / "logs"
_LOGS_DIR.mkdir(parents=True, exist_ok=True)

_LOG_FILE_PATH = _LOGS_DIR / "analysis.log"
_DEFAULT_LOG_LEVEL = logging.INFO

# Global logger instance
_logger: Optional[logging.Logger] = None


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Retrieve or create a configured logger instance.
    
    Args:
        name: Optional name for the logger. If None, returns the root logger.
    
    Returns:
        A configured logging.Logger instance.
    """
    global _logger
    
    if _logger is None:
        _logger = _setup_root_logger()
    
    if name:
        return _logger.getChild(name)
    return _logger


def _setup_root_logger() -> logging.Logger:
    """
    Configure the root logger with file and console handlers.
    
    Returns:
        The configured root logger.
    """
    root_logger = logging.getLogger()
    
    # Prevent duplicate handlers if called multiple times
    if root_logger.handlers:
        # Clear existing handlers to ensure fresh configuration
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
    
    root_logger.setLevel(_DEFAULT_LOG_LEVEL)
    
    # Define format for structured output
    log_format = (
        "%(asctime)s | %(levelname)-8s | %(name)s | "
        "%(filename)s:%(lineno)d | %(message)s"
    )
    formatter = logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")
    
    # File handler: writes to logs/analysis.log
    file_handler = logging.FileHandler(_LOG_FILE_PATH)
    file_handler.setLevel(_DEFAULT_LOG_LEVEL)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # Console handler: writes to stdout
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(_DEFAULT_LOG_LEVEL)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    return root_logger


def reset_logging_config(log_level: int = _DEFAULT_LOG_LEVEL, log_file: Optional[Path] = None) -> None:
    """
    Reset logging configuration with optional customizations.
    
    Args:
        log_level: The logging level to set (default: INFO).
        log_file: Optional custom path for the log file.
    """
    global _logger, _LOG_FILE_PATH
    
    if log_file:
        _LOG_FILE_PATH = log_file
        # Ensure directory exists
        _LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    _logger = None  # Reset to force re-initialization
    _setup_root_logger()
    logging.getLogger().setLevel(log_level)


# Convenience function for immediate use
def setup_logging() -> logging.Logger:
    """
    Initialize logging infrastructure and return the root logger.
    
    This function should be called once at the entry point of any analysis script.
    
    Returns:
        The configured root logger.
    """
    return get_logger()

# Example usage demonstration (only runs if executed directly)
if __name__ == "__main__":
    # Initialize logging
    logger = setup_logging()
    
    # Demonstrate logging levels
    logger.debug("This is a DEBUG message - typically suppressed at INFO level")
    logger.info("This is an INFO message - standard operational logging")
    logger.warning("This is a WARNING message - potential issues")
    logger.error("This is an ERROR message - error conditions")
    logger.critical("This is a CRITICAL message - severe errors")
    
    print(f"\nLog file created at: {_LOG_FILE_PATH}")
    print("Logging infrastructure initialized successfully.")