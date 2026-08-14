"""
Logging configuration and utility functions for the Power Drift Detection pipeline.
Ensures consistent logging format, file handlers, and level management across all modules.
"""
import os
import logging
import sys
from pathlib import Path
from datetime import datetime

# Constants
LOG_DIR = Path("state")
LOG_FILE_NAME = "pipeline_execution.log"
DEFAULT_LEVEL = logging.INFO

# Ensure log directory exists
LOG_DIR.mkdir(parents=True, exist_ok=True)

def setup_logging():
    """
    Configures the root logger with a console handler and a file handler.
    Sets the log format to include timestamp, level, module, and message.
    """
    logger = logging.getLogger()
    logger.setLevel(DEFAULT_LEVEL)

    # Clear existing handlers to avoid duplicates in repeated runs
    if logger.handlers:
        logger.handlers.clear()

    # Define format
    log_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(DEFAULT_LEVEL)
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)

    # File Handler
    log_file_path = LOG_DIR / LOG_FILE_NAME
    file_handler = logging.FileHandler(log_file_path, mode='a')
    file_handler.setLevel(DEFAULT_LEVEL)
    file_handler.setFormatter(log_format)
    logger.addHandler(file_handler)

    logger.info("Logging system initialized.")
    return logger

def get_module_logger(name: str) -> logging.Logger:
    """
    Retrieves a logger specific to a module name.
    """
    return logging.getLogger(name)

def log_data_filtering_step(logger: logging.Logger, step_name: str, rows_before: int, rows_after: int, reason: str):
    """
    Logs a standardized message about data filtering steps.
    """
    rows_removed = rows_before - rows_after
    logger.info(
        f"FILTER: {step_name} - Removed {rows_removed} rows ({reason}). "
        f"Rows remaining: {rows_after} (Start: {rows_before})"
    )

def log_operation_start(logger: logging.Logger, operation_name: str):
    """
    Logs the start of a major operation.
    """
    logger.info(f"START: {operation_name}")

def log_operation_complete(logger: logging.Logger, operation_name: str, success: bool = True, details: str = ""):
    """
    Logs the completion of a major operation.
    """
    status = "SUCCESS" if success else "FAILED"
    msg = f"END: {operation_name} - {status}"
    if details:
        msg += f" | {details}"
    logger.info(msg)
