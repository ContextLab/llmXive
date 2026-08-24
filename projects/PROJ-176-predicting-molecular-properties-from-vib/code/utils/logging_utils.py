import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

def setup_logging(
    log_level: int = logging.INFO,
    log_file: Optional[str] = None,
    name: Optional[str] = None
) -> logging.Logger:
    """
    Setup logging configuration.
    
    Args:
        log_level: Logging level (e.g., logging.INFO)
        log_file: Optional path to log file
        name: Logger name
        
    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the given name.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        setup_logging(name=name)
    return logger

def log_data_ingestion_step(step_name: str, count: Optional[int] = None, message: Optional[str] = None):
    """
    Log a data ingestion step.
    
    Args:
        step_name: Name of the step
        count: Optional count (e.g., number of records processed)
        message: Optional additional message
    """
    logger = get_logger("data.ingestion")
    log_msg = f"Step: {step_name}"
    if count is not None:
        log_msg += f" | Count: {count}"
    if message:
        log_msg += f" | {message}"
    logger.info(log_msg)

def log_coverage_audit_result(p_value: float, threshold: float = 0.05):
    """
    Log the result of a coverage audit (KS-test).
    
    Args:
        p_value: P-value from the test
        threshold: Significance threshold
    """
    logger = get_logger("data.audit")
    status = "PASS" if p_value >= threshold else "WARNING (Selection Bias Detected)"
    logger.info(f"Coverage Audit Result: {status} (p-value: {p_value:.4f}, threshold: {threshold})")
