import os
import logging
import sys
from pathlib import Path
from datetime import datetime

def setup_logging():
    """
    Sets up the logging configuration for the project.
    
    Returns:
        Logger instance.
    """
    logger = logging.getLogger("llmXive")
    logger.setLevel(logging.INFO)
    
    # Avoid adding handlers multiple times
    if not logger.handlers:
        # Console handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        ch.setFormatter(formatter)
        
        logger.addHandler(ch)
    
    return logger

def get_module_logger(name: str) -> logging.Logger:
    """
    Gets a logger for a specific module.
    
    Args:
        name: Module name (usually __name__).
        
    Returns:
        Logger instance.
    """
    logger = logging.getLogger(f"llmXive.{name}")
    # Propagate to root handler
    logger.propagate = True
    return logger

def log_operation_start(logger: logging.Logger, operation: str):
    """
    Logs the start of an operation.
    
    Args:
        logger: Logger instance.
        operation: Name of the operation.
    """
    logger.info(f"Starting operation: {operation}")

def log_operation_complete(logger: logging.Logger, operation: str):
    """
    Logs the completion of an operation.
    
    Args:
        logger: Logger instance.
        operation: Name of the operation.
    """
    logger.info(f"Completed operation: {operation}")

def log_data_filter_step(
    logger: logging.Logger, 
    input_path: str, 
    output_path: str, 
    rows_before: int, 
    rows_after: int, 
    reason: str
):
    """
    Logs the details of a data filtering step.
    
    Args:
        logger: Logger instance.
        input_path: Path to input data.
        output_path: Path to output data.
        rows_before: Number of rows before filtering.
        rows_after: Number of rows after filtering.
        reason: Reason for filtering.
    """
    removed_count = rows_before - rows_after
    logger.info(
        f"Data Filter: {input_path} -> {output_path} | "
        f"Rows: {rows_before} -> {rows_after} (Removed {removed_count}) | "
        f"Reason: {reason}"
    )

def log_skipped_row(logger: logging.Logger, row_index: int, reason: str):
    """
    Logs a skipped row during data processing.
    
    Args:
        logger: Logger instance.
        row_index: Index of the skipped row.
        reason: Reason for skipping.
    """
    logger.warning(f"WARNING: Skipping row {row_index} due to {reason}")

def log_zero_variance_field(logger: logging.Logger, field_name: str, count: int):
    """
    Logs a warning about a grouping field with zero variance or single level.
    
    Args:
        logger: Logger instance.
        field_name: Name of the field.
        count: Number of unique levels found.
    """
    logger.warning(
        f"Grouping field '{field_name}' has only {count} unique level(s). "
        "This may cause convergence issues in mixed-effects models."
    )
