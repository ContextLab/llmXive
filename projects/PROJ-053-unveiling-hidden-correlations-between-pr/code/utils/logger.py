import logging
import time
import json
import os
from contextlib import contextmanager
from typing import Optional, Dict, Any
from pathlib import Path

from config import get_results_dir, ensure_directories, get_logs_dir, get_logger

def setup_logging(
    log_file: Optional[str] = None,
    level: int = logging.INFO,
    name: str = "root"
) -> logging.Logger:
    """
    Configure logging for the project.
    
    Args:
        log_file: Optional path to log file. If None, logs to console only.
        level: Logging level (e.g., logging.INFO, logging.DEBUG).
        name: Logger name.
        
    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Clear existing handlers to avoid duplicates
    if logger.handlers:
        logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        ensure_directories()
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger

@contextmanager
def log_execution_time(
    operation_name: str,
    logger: Optional[logging.Logger] = None
):
    """
    Context manager to log the execution time of a block of code.
    
    Args:
        operation_name: Name of the operation being timed.
        logger: Logger instance. If None, uses default logger.
        
    Yields:
        None
    """
    if logger is None:
        logger = get_logger("pipeline")
        
    start_time = time.time()
    logger.info(f"Starting operation: {operation_name}")
    
    try:
        yield
    finally:
        end_time = time.time()
        duration = end_time - start_time
        logger.info(f"Completed operation: {operation_name} in {duration:.2f} seconds")

def log_error_and_raise(
    logger: logging.Logger,
    message: str,
    exception_type: Exception = RuntimeError
):
    """
    Log an error message and raise an exception.
    
    Args:
        logger: Logger instance.
        message: Error message.
        exception_type: Type of exception to raise.
        
    Raises:
        exception_type: The specified exception with the provided message.
    """
    logger.error(message)
    raise exception_type(message)

def get_log_file_path(log_name: str = "pipeline") -> str:
    """
    Get the full path for a log file.
    
    Args:
        log_name: Name of the log file (without extension).
        
    Returns:
        Full path to the log file.
    """
    ensure_directories()
    logs_dir = get_logs_dir()
    return str(Path(logs_dir) / f"{log_name}.log")

def save_runtime_metrics(metrics: Dict[str, Any]) -> None:
    """
    Save runtime metrics to results/metrics.json, merging with existing data if present.
    
    This function ensures that runtime metrics are ALWAYS saved, regardless of 
    pipeline outcome (SC-005 compliance).
    
    Args:
        metrics: Dictionary containing metrics to save. Expected keys:
            - total_runtime_seconds (float): Total execution time in seconds.
            - time_limit_seconds (float): Configured time limit.
            - status (str): 'PASS' or 'FAIL' based on time limit check.
            - Other metrics may be included as needed.
    """
    ensure_directories()
    results_dir = get_results_dir()
    metrics_path = Path(results_dir) / "metrics.json"
    
    # Load existing metrics if file exists
    existing_metrics = {}
    if metrics_path.exists():
        try:
            with open(metrics_path, 'r') as f:
                existing_metrics = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logging.warning(f"Could not read existing metrics.json: {e}. Starting fresh.")
    
    # Merge new metrics with existing
    existing_metrics.update(metrics)
    
    # Save updated metrics
    with open(metrics_path, 'w') as f:
        json.dump(existing_metrics, f, indent=2)
    
    logging.info(f"Runtime metrics saved to {metrics_path}")