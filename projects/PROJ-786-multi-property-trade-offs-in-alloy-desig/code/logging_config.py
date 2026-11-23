"""
Logging configuration module for the llmXive project.

This module sets up a global logger with JSON formatting and file rotation
as required by task T008. It re-uses the infrastructure from utils/logging_config.py
to ensure consistency across the project.
"""

import os
import logging
from pathlib import Path
from utils.logging_config import (
    configure_root_logger,
    get_logger,
    log_info_with_context,
    log_warning_with_context,
    log_error_with_context,
    log_critical_with_context,
    StructuredFormatter,
)

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent
LOG_DIR = PROJECT_ROOT / "data" / "logs"
LOG_FILE = LOG_DIR / "pipeline.log"

# Ensure log directory exists
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Configure the root logger with file rotation
configure_root_logger(
    log_level=logging.INFO,
    log_file=str(LOG_FILE),
    max_bytes=10 * 1024 * 1024,  # 10MB
    backup_count=5,
)

# Global logger instance
logger = get_logger("llmXive")

# Convenience functions for logging
def log_info(message: str, context: dict = None, trace_id: str = None) -> None:
    """Log an info message with context."""
    log_info_with_context(logger, message, context, trace_id)

def log_warning(message: str, context: dict = None, trace_id: str = None) -> None:
    """Log a warning message with context."""
    log_warning_with_context(logger, message, context, trace_id)

def log_error(message: str, context: dict = None, trace_id: str = None) -> None:
    """Log an error message with context."""
    log_error_with_context(logger, message, context, trace_id)

def log_critical(message: str, context: dict = None, trace_id: str = None) -> None:
    """Log a critical message with context."""
    log_critical_with_context(logger, message, context, trace_id)

def log_debug(message: str, context: dict = None, trace_id: str = None) -> None:
    """Log a debug message with context."""
    logging.getLogger("llmXive").debug(message, extra={"context": context or {}, "trace_id": trace_id or str(__import__('uuid').uuid4())})

# Initialize the logger on module load
log_info("Logging infrastructure initialized", {"log_file": str(LOG_FILE)})

if __name__ == "__main__":
    # Test the logging configuration
    log_info("Test info message")
    log_warning("Test warning message", {"test_key": "test_value"})
    log_error("Test error message", {"error_code": 500})
    log_critical("Test critical message")
    log_debug("Test debug message")
