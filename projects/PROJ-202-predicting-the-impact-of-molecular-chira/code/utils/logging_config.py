"""
Logging configuration and utilities for the llmXive pipeline.

This module provides a centralized logging setup that writes to
data/logs/pipeline.log and also outputs to stdout/stderr.
"""
import logging
import os
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

# Import Config from the existing settings module
from code.config.settings import Config

# Ensure the log directory exists
LOG_DIR = Path(Config.LOG_DIR)
LOG_FILE = LOG_DIR / "pipeline.log"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Global logger instance
_logger: Optional[logging.Logger] = None


def setup_logging(
    log_file: Optional[Path] = None,
    level: int = logging.INFO,
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5,
) -> None:
    """
    Configure the root logger for the pipeline.
    
    Sets up:
    - A rotating file handler writing to data/logs/pipeline.log
    - A stream handler for stdout/stderr
    
    Args:
        log_file: Path to the log file. Defaults to Config.LOG_DIR/pipeline.log.
        level: Logging level (e.g., logging.DEBUG, logging.INFO).
        max_bytes: Maximum size of a log file before rotation.
        backup_count: Number of backup files to keep.
    """
    global _logger
    
    if log_file is None:
        log_file = LOG_FILE
    
    # Ensure directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    
    # Stream handler for stdout
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(level)
    stream_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    root_logger.addHandler(file_handler)
    root_logger.addHandler(stream_handler)
    
    _logger = root_logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance, ensuring logging is configured first.
    
    Args:
        name: Logger name (e.g., module name). If None, returns the root logger.
    
    Returns:
        A configured logging.Logger instance.
    """
    global _logger
    
    # Ensure logging is set up if not already done
    if _logger is None:
        setup_logging()
    
    if name:
        return logging.getLogger(name)
    return _logger


def log_pipeline_start(
    pipeline_name: str,
    config_summary: Optional[dict] = None,
) -> None:
    """
    Log the start of a pipeline run.
    
    Args:
        pipeline_name: Name of the pipeline being executed.
        config_summary: Optional dictionary of configuration values to log.
    """
    logger = get_logger("pipeline")
    logger.info("=" * 60)
    logger.info(f"Pipeline '{pipeline_name}' starting.")
    if config_summary:
        logger.info("Configuration:")
        for key, value in config_summary.items():
            logger.info(f"  {key}: {value}")
    logger.info("=" * 60)


def log_pipeline_end(
    pipeline_name: str,
    status: str,
    message: Optional[str] = None,
) -> None:
    """
    Log the end of a pipeline run.
    
    Args:
        pipeline_name: Name of the pipeline.
        status: Final status (e.g., 'SUCCESS', 'FAILED').
        message: Optional additional message.
    """
    logger = get_logger("pipeline")
    logger.info("=" * 60)
    logger.info(f"Pipeline '{pipeline_name}' ended with status: {status}")
    if message:
        logger.info(f"Message: {message}")
    logger.info("=" * 60)


def log_error_occurrence(
    error_type: str,
    error_message: str,
    context: Optional[dict] = None,
) -> None:
    """
    Log an error occurrence with optional context.
    
    Args:
        error_type: Type of error (e.g., 'ValueError', 'FileNotFoundError').
        error_message: The error message.
        context: Optional dictionary of contextual information.
    """
    logger = get_logger("pipeline")
    logger.error(f"{error_type}: {error_message}")
    if context:
        logger.error("Context:")
        for key, value in context.items():
            logger.error(f"  {key}: {value}")

# Initialize logging on module import if desired, or wait for explicit call
# setup_logging() # Uncomment to auto-initialize on import
