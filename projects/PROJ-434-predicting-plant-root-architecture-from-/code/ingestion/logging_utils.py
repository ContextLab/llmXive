import os
import logging
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

def setup_logging(log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Configure root logger with console and optional file handlers.
    
    Args:
        log_file: Optional path to write logs. If None, only console output is used.
        level: Logging level (e.g., logging.INFO, logging.DEBUG).
    
    Returns:
        The configured root logger.
    """
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # Clear existing handlers to avoid duplicates in interactive environments
    if logger.handlers:
        logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(console_format)
        logger.addHandler(file_handler)
    
    return logger

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name. If None, returns the root logger.
    
    Returns:
        A configured logger.
    """
    if name is None:
        return logging.getLogger()
    return logging.getLogger(name)

def log_excluded_record(
    logger: logging.Logger,
    record_id: str,
    reason: str,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log a single excluded record with specific reason.
    
    Args:
        logger: Logger instance to use.
        record_id: Unique identifier for the record (e.g., row index, sample ID).
        reason: Specific reason for exclusion (e.g., 'missing soil data', 'failed geocoding').
        details: Optional dictionary of additional context (coordinates, values, etc.).
    """
    msg = f"EXCLUDED_RECORD: ID={record_id}, REASON={reason}"
    if details:
        detail_str = ", ".join(f"{k}={v}" for k, v in details.items())
        msg += f" | DETAILS: {detail_str}"
    logger.warning(msg)

def log_species_exclusion_summary(
    logger: logging.Logger,
    species_name: str,
    observation_count: int,
    threshold: int,
    reason: str
) -> None:
    """
    Log the exclusion of a species due to low sample size or other filters.
    
    Args:
        logger: Logger instance to use.
        species_name: Name of the species being excluded.
        observation_count: Number of valid observations found for this species.
        threshold: Minimum required observations.
        reason: Specific reason for exclusion (e.g., 'observation_count < 10').
    """
    msg = (
        f"EXCLUDED_SPECIES: species={species_name}, "
        f"count={observation_count}, threshold={threshold}, REASON={reason}"
    )
    logger.warning(msg)

def log_validation_failure(
    logger: logging.Logger,
    metric_name: str,
    observed_value: float,
    threshold: float,
    message: Optional[str] = None
) -> None:
    """
    Log a validation failure when a metric does not meet the required threshold.
    
    Args:
        logger: Logger instance to use.
        metric_name: Name of the metric being validated.
        observed_value: The actual value observed.
        threshold: The required threshold value.
        message: Optional additional context message.
    """
    msg = (
        f"VALIDATION_FAILED: metric={metric_name}, "
        f"observed={observed_value:.4f}, threshold={threshold:.4f}"
    )
    if message:
        msg += f" | MESSAGE: {message}"
    logger.error(msg)
