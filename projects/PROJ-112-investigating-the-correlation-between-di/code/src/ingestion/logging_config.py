import logging
import sys
from typing import Dict, Any, Optional
from pathlib import Path
from src.utils.logger import get_logger

# Constants for log file locations
LOG_DIR = Path("data/processed/results")
INGESTION_LOG_FILE = "ingestion_pipeline.log"

_logger_instance: Optional[logging.Logger] = None

def get_ingestion_logger() -> logging.Logger:
    """
    Returns a singleton logger instance configured for ingestion tasks.
    Logs are written to data/processed/results/ingestion_pipeline.log
    and also to stdout/stderr.
    """
    global _logger_instance
    if _logger_instance is None:
        logger = get_logger("ingestion_pipeline")
        
        # Ensure log directory exists
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        
        # File handler
        file_handler = logging.FileHandler(LOG_DIR / INGESTION_LOG_FILE)
        file_handler.setLevel(logging.INFO)
        file_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_format)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_format)
        
        # Add handlers if not already present (avoid duplication on cache hit)
        if not logger.handlers:
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)
        
        _logger_instance = logger
    
    return _logger_instance

def log_download_status(
    source_name: str, 
    status: str, 
    details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Logs the status of a data download operation.
    
    Args:
        source_name: Name of the data source (e.g., 'AGP', 'UKBB')
        status: Status string (e.g., 'STARTED', 'COMPLETED', 'FAILED')
        details: Optional dict with extra info (size, checksum, duration)
    """
    logger = get_ingestion_logger()
    msg = f"Download [{source_name}]: {status}"
    if details:
        msg += f" | Details: {details}"
    
    if status == "FAILED":
        logger.error(msg)
    elif status == "COMPLETED":
        logger.info(msg)
    else:
        logger.info(msg)

def log_filter_counts(
    step_name: str, 
    initial_count: int, 
    filtered_count: int, 
    reason: str
) -> None:
    """
    Logs the results of a filtering step.
    
    Args:
        step_name: Name of the filtering step (e.g., 'Read Count Filter', 'Fiber Range Filter')
        initial_count: Number of samples before filtering
        filtered_count: Number of samples after filtering
        reason: Description of the filter criteria
    """
    logger = get_ingestion_logger()
    removed = initial_count - filtered_count
    logger.info(
        f"Filter [{step_name}]: {initial_count} -> {filtered_count} "
        f"(Removed: {removed}, Reason: {reason})"
    )

def log_harmonization_result(
    metric_name: str, 
    value: Any, 
    unit: Optional[str] = None
) -> None:
    """
    Logs a harmonization metric result.
    
    Args:
        metric_name: Name of the metric (e.g., 'Fiber Unit Conversion', 'Read Count Normalization')
        value: The calculated value
        unit: Optional unit string
    """
    logger = get_ingestion_logger()
    unit_str = f" ({unit})" if unit else ""
    logger.info(f"Harmonization [{metric_name}]: {value}{unit_str}")

def log_merge_result(
    agp_count: int, 
    ukbb_count: int, 
    total_count: int, 
    duplicates: int = 0
) -> None:
    """
    Logs the result of merging datasets.
    
    Args:
        agp_count: Number of AGP samples
        ukbb_count: Number of UKBB samples
        total_count: Total merged sample count
        duplicates: Number of duplicate samples found (if any)
    """
    logger = get_ingestion_logger()
    logger.info(
        f"Merge Result: AGP={agp_count}, UKBB={ukbb_count}, Total={total_count}"
    )
    if duplicates > 0:
        logger.warning(f"Duplicate samples detected: {duplicates}")

def log_validation_result(
    check_name: str, 
    passed: bool, 
    details: Optional[str] = None
) -> None:
    """
    Logs the result of a validation check.
    
    Args:
        check_name: Name of the check (e.g., 'PII Scan', 'Schema Validation')
        passed: Boolean indicating if the check passed
        details: Optional details about the failure or success
    """
    logger = get_ingestion_logger()
    status = "PASSED" if passed else "FAILED"
    msg = f"Validation [{check_name}]: {status}"
    if details:
        msg += f" | {details}"
    
    if passed:
        logger.info(msg)
    else:
        logger.error(msg)
