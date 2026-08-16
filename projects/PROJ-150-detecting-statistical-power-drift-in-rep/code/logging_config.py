import os
import logging
import sys
from pathlib import Path
from datetime import datetime

def setup_logging(log_dir: str = "logs", level: int = logging.INFO) -> logging.Logger:
    """
    Sets up the root logger and creates a log file with a timestamped name.
    
    Args:
        log_dir: Directory to store log files. Defaults to 'logs'.
        level: Logging level (e.g., logging.INFO, logging.DEBUG).
        
    Returns:
        The configured root logger.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers to avoid duplicates
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # Create logs directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = Path(log_dir) / f"pipeline_{timestamp}.log"

    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)
    file_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_format)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_format = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    console_handler.setFormatter(console_format)

    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    return root_logger

def get_module_logger(module_name: str) -> logging.Logger:
    """
    Retrieves a logger for a specific module.
    
    Args:
        module_name: The name of the module (usually __name__).
        
    Returns:
        A logger instance for the module.
    """
    return logging.getLogger(module_name)

def log_operation_start(logger: logging.Logger, operation_name: str):
    """
    Logs the start of a major operation.
    
    Args:
        logger: The logger to use.
        operation_name: Name of the operation starting.
    """
    logger.info(f"--- STARTING OPERATION: {operation_name} ---")

def log_operation_complete(logger: logging.Logger, operation_name: str):
    """
    Logs the successful completion of a major operation.
    
    Args:
        logger: The logger to use.
        operation_name: Name of the operation completed.
    """
    logger.info(f"--- COMPLETED OPERATION: {operation_name} ---")

def log_data_filter_step(logger: logging.Logger, source_file: str, target_file: str, rows_before: int, rows_after: int, filter_criteria: str):
    """
    Logs details of a data filtering step.
    
    Args:
        logger: The logger to use.
        source_file: Path to the source file.
        target_file: Path to the output file.
        rows_before: Number of rows before filtering.
        rows_after: Number of rows after filtering.
        filter_criteria: Description of the filter applied.
    """
    logger.info(f"Data Filtering Step: {filter_criteria}")
    logger.info(f"  Source: {source_file}")
    logger.info(f"  Target: {target_file}")
    logger.info(f"  Rows before: {rows_before}")
    logger.info(f"  Rows after: {rows_after}")
    logger.info(f"  Rows removed: {rows_before - rows_after}")

def log_skipped_row(logger: logging.Logger, row_index: int, reason: str):
    """
    Logs a warning for a skipped row due to data issues.
    Format: WARNING: Skipping row {index} due to {reason}
    
    Args:
        logger: The logger to use.
        row_index: Index of the skipped row.
        reason: Reason for skipping (e.g., 'NaN in effect_size').
    """
    logger.warning(f"WARNING: Skipping row {row_index} due to {reason}")

def log_zero_variance_field(logger: logging.Logger, field_name: str, unique_levels: int):
    """
    Logs a warning when a grouping field has zero variance or insufficient levels.
    
    Args:
        logger: The logger to use.
        field_name: Name of the field with issues.
        unique_levels: Number of unique levels found.
    """
    logger.warning(f"WARNING: Field '{field_name}' has only {unique_levels} unique level(s) or zero variance. Excluding from random effects.")
