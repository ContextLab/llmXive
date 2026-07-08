"""
Logging utilities for the llmXive research pipeline.

This module configures logging infrastructure and provides helpers to
retrieve log file paths. It integrates with security.py to ensure
no PII is leaked in logs.
"""
import logging
import os
from pathlib import Path
from typing import Optional

from config import get_logs_dir, get_log_file_path as config_get_log_file_path, \
                   get_error_log_file_path as config_get_error_log_file_path, \
                   get_manipulation_error_log_path as config_get_manipulation_error_log_path
from utils.security import SanitizedLogger, sanitize_log_message

# Ensure logs directory exists
LOGS_DIR = get_logs_dir()
if LOGS_DIR and not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR, exist_ok=True)

def get_logger(name: str) -> SanitizedLogger:
    """
    Get a logger instance that automatically sanitizes messages to prevent PII leakage.
    
    Args:
        name: The name of the logger (usually __name__).
        
    Returns:
        A SanitizedLogger instance configured to write to the project logs.
    """
    # Get the base logger
    base_logger = logging.getLogger(name)
    
    # Avoid adding handlers multiple times if called repeatedly
    if not base_logger.handlers:
        base_logger.setLevel(logging.DEBUG)
        
        # File handler for general logs
        log_file = config_get_log_file_path()
        if log_file:
            fh = logging.FileHandler(log_file)
            fh.setLevel(logging.INFO)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            fh.setFormatter(formatter)
            base_logger.addHandler(fh)
        
        # Console handler for errors and warnings
        ch = logging.StreamHandler()
        ch.setLevel(logging.WARNING)
        ch.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        base_logger.addHandler(ch)
        
        # Prevent propagation to root logger to avoid double logging
        base_logger.propagate = False
    
    return SanitizedLogger(base_logger, {})

def get_log_file_path() -> Optional[str]:
    """Get the path to the main log file."""
    return config_get_log_file_path()

def get_error_log_file_path() -> Optional[str]:
    """Get the path to the error-specific log file."""
    return config_get_error_log_file_path()

def get_manipulation_error_log_path() -> Optional[str]:
    """Get the path to the manipulation error log file."""
    return config_get_manipulation_error_log_path()

def sanitize_message(message: str) -> str:
    """
    Utility to manually sanitize a string before logging if not using SanitizedLogger.
    
    Args:
        message: The message to sanitize.
        
    Returns:
        The sanitized message.
    """
    return sanitize_log_message(message)

def setup_logging():
    """
    Initialize the logging infrastructure.
    
    This ensures directories exist and basic handlers are configured.
    """
    if LOGS_DIR:
        os.makedirs(LOGS_DIR, exist_ok=True)
    # Logger creation triggers handler setup
    get_logger("system")

if __name__ == "__main__":
    # Test the logger
    logger = get_logger("test")
    logger.info("This is a test message.")
    logger.warning("Warning: Test warning.")
    logger.error("Error: Test error.")
    # Simulate PII leak attempt
    logger.info("User email test@example.com was logged.")
