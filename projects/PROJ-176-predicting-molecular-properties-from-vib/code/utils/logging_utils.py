"""
Logging utilities for the molecular properties prediction pipeline.

This module provides centralized logging configuration and helper functions
to ensure consistent logging across all data ingestion, preprocessing, and
model training steps.
"""
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# Configure a default logger for the project
PROJECT_LOGGER_NAME = "llmXive.molecular_properties"

def setup_logging(
    log_file: Optional[str] = None,
    level: int = logging.INFO,
    project_root: Optional[Path] = None
) -> logging.Logger:
    """
    Configure and return the project's main logger.
    
    Args:
        log_file: Optional path to a log file. If None, logs only to stderr.
        level: Logging level (e.g., logging.DEBUG, logging.INFO).
        project_root: Base directory for the project. Used to resolve relative log paths.
    
    Returns:
        A configured logging.Logger instance.
    """
    logger = logging.getLogger(PROJECT_LOGGER_NAME)
    logger.setLevel(level)
    
    # Clear any existing handlers to avoid duplicates
    if logger.handlers:
        logger.handlers.clear()
    
    # Formatter with timestamp, level, and message
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler (always present)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        log_path = Path(log_file)
        if project_root and not log_path.is_absolute():
            log_path = project_root / log_file
        
        # Ensure log directory exists
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(str(log_path))
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance, optionally with a sub-namespace.
    
    Args:
        name: Optional sub-namespace (e.g., 'data.download', 'models.trainer').
    
    Returns:
        A logging.Logger instance.
    """
    if name:
        return logging.getLogger(f"{PROJECT_LOGGER_NAME}.{name}")
    return logging.getLogger(PROJECT_LOGGER_NAME)

def log_data_ingestion_step(
    logger: logging.Logger,
    step_name: str,
    input_count: Optional[int] = None,
    output_count: Optional[int] = None,
    discarded_count: Optional[int] = None,
    mismatch_count: Optional[int] = None,
    message: Optional[str] = None
) -> None:
    """
    Log a standardized data ingestion step with counts.
    
    This function ensures consistent logging format for data pipeline steps,
    particularly useful for tracking dataset alignment, filtering, and
    preprocessing operations.
    
    Args:
        logger: The logger instance to use.
        step_name: Name of the step (e.g., 'align_datasets', 'filter_properties').
        input_count: Number of records before the step.
        output_count: Number of records after the step.
        discarded_count: Number of records discarded (e.g., due to missing keys).
        mismatch_count: Number of records with mismatched metadata.
        message: Optional additional message.
    """
    log_parts = [f"Step: {step_name}"]
    
    if input_count is not None:
        log_parts.append(f"Input: {input_count}")
    
    if output_count is not None:
        log_parts.append(f"Output: {output_count}")
    
    if discarded_count is not None:
        log_parts.append(f"Discarded: {discarded_count}")
    
    if mismatch_count is not None:
        log_parts.append(f"Mismatches: {mismatch_count}")
    
    if message:
        log_parts.append(message)
    
    log_message = " | ".join(log_parts)
    
    # Determine log level based on discarded/mismatch counts
    if discarded_count and discarded_count > 0:
        logger.warning(log_message)
    elif mismatch_count and mismatch_count > 0:
        logger.warning(log_message)
    else:
        logger.info(log_message)

def log_coverage_audit_result(
    logger: logging.Logger,
    property_name: str,
    p_value: float,
    threshold: float = 0.05
) -> None:
    """
    Log the result of a coverage audit (KS-test) for a property.
    
    Args:
        logger: The logger instance to use.
        property_name: Name of the property being audited.
        p_value: P-value from the statistical test.
        threshold: Significance threshold (default 0.05).
    """
    if p_value < threshold:
        logger.warning(
            f"Coverage Audit: Property '{property_name}' shows significant "
            f"distribution shift (p={p_value:.4f} < {threshold}). "
            "Selection bias detected."
        )
    else:
        logger.info(
            f"Coverage Audit: Property '{property_name}' distribution consistent "
            f"(p={p_value:.4f} >= {threshold}). No significant bias detected."
        )