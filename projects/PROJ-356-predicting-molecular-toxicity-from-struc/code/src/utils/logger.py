"""
Logging infrastructure for the molecular toxicity prediction pipeline.

This module provides a configured logger that captures:
- Data counts (records processed, filtered, etc.)
- Errors (exceptions, validation failures)
- Checksums (data integrity verification)

All logs are written to both console and file handlers.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

# Project root relative to this file
# code/src/utils/logger.py -> project root is 3 levels up
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# Default log file path
DEFAULT_LOG_FILE = PROJECT_ROOT / "data" / "pipeline.log"

# Log format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Singleton logger instance
_logger: Optional[logging.Logger] = None


def get_logger(name: str = "toxicity_pipeline") -> logging.Logger:
    """
    Get or create the project logger with configured handlers.
    
    Args:
        name: Logger name (default: "toxicity_pipeline")
        
    Returns:
        Configured logging.Logger instance
    """
    global _logger
    
    if _logger is not None and _logger.name == name:
        return _logger
    
    # Create new logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        return logger
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    
    # Create file handler (ensure data directory exists)
    log_file_path = DEFAULT_LOG_FILE
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    
    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    # Store reference
    _logger = logger
    
    return logger


def log_data_count(
    logger: logging.Logger,
    source: str,
    count: int,
    operation: str = "processed",
    details: Optional[str] = None
) -> None:
    """
    Log data count information.
    
    Args:
        logger: Logger instance
        source: Data source name (e.g., "ToxCast", "PubChem")
        count: Number of records
        operation: Operation performed (e.g., "loaded", "filtered", "duplicated_removed")
        details: Optional additional details
    """
    msg = f"DATA_COUNT: source={source}, operation={operation}, count={count}"
    if details:
        msg += f", details={details}"
    logger.info(msg)


def log_error(
    logger: logging.Logger,
    error_type: str,
    message: str,
    context: Optional[dict] = None
) -> None:
    """
    Log error information with context.
    
    Args:
        logger: Logger instance
        error_type: Type of error (e.g., "ValidationError", "DownloadError")
        message: Error message
        context: Optional context dictionary (e.g., file paths, parameters)
    """
    msg = f"ERROR: type={error_type}, message={message}"
    if context:
        context_str = ", ".join(f"{k}={v}" for k, v in context.items())
        msg += f", context={{{context_str}}}"
    logger.error(msg)


def log_checksum(
    logger: logging.Logger,
    file_path: str,
    checksum: str,
    algorithm: str = "sha256"
) -> None:
    """
    Log file checksum for integrity verification.
    
    Args:
        logger: Logger instance
        file_path: Path to the file
        checksum: Checksum value
        algorithm: Hash algorithm used (default: "sha256")
    """
    msg = f"CHECKSUM: file={file_path}, algorithm={algorithm}, hash={checksum}"
    logger.info(msg)


def log_pipeline_stage(
    logger: logging.Logger,
    stage: str,
    status: str,
    duration_seconds: Optional[float] = None,
    metrics: Optional[dict] = None
) -> None:
    """
    Log pipeline stage execution.
    
    Args:
        logger: Logger instance
        stage: Stage name (e.g., "download", "preprocess", "training")
        status: Status (e.g., "started", "completed", "failed")
        duration_seconds: Optional duration in seconds
        metrics: Optional metrics dictionary
    """
    msg = f"PIPELINE: stage={stage}, status={status}"
    if duration_seconds is not None:
        msg += f", duration={duration_seconds:.2f}s"
    if metrics:
        metrics_str = ", ".join(f"{k}={v}" for k, v in metrics.items())
        msg += f", metrics={{{metrics_str}}}"
    logger.info(msg)


# Convenience function for immediate use
def setup_default_logger() -> logging.Logger:
    """
    Setup and return the default project logger.
    
    Returns:
        Configured logging.Logger instance
    """
    return get_logger("toxicity_pipeline")
