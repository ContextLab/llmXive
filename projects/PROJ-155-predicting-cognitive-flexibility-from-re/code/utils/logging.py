import os
import logging
import json
import sys
from datetime import datetime
from typing import Optional, Dict, Any, List

from code.data.paths import get_processed_path, ensure_dir

class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging output."""
    
    def format(self, record):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName
        }
        if hasattr(record, 'extra_data'):
            log_entry.update(record.extra_data)
        return json.dumps(log_entry)

def init_logging(log_level: int = logging.INFO, log_file: Optional[str] = None) -> logging.Logger:
    """
    Initialize the logging system.
    
    Args:
        log_level: The logging level.
        log_file: Optional path to a log file.
    
    Returns:
        The root logger.
    """
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Clear existing handlers
    logger.handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        ensure_dir(os.path.dirname(log_file))
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_formatter = StructuredFormatter()
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_exclusion_log_path() -> str:
    """
    Get the path to the exclusion log CSV.
    
    Returns:
        Absolute path to data/processed/exclusion_log.csv.
    """
    processed_path = get_processed_path()
    return os.path.join(processed_path, "exclusion_log.csv")

def get_error_log_path() -> str:
    """
    Get the path to the error log file.
    
    Returns:
        Absolute path to data/processed/error_log.jsonl.
    """
    processed_path = get_processed_path()
    return os.path.join(processed_path, "error_log.jsonl")

def log_exclusion(subject_id: str, reason: str, details: Optional[Dict[str, Any]] = None) -> None:
    """
    Log an exclusion event.
    
    Args:
        subject_id: The subject identifier.
        reason: The reason for exclusion.
        details: Optional additional details.
    """
    logger = logging.getLogger(__name__)
    log_entry = {
        "subject_id": subject_id,
        "reason": reason,
        "timestamp": datetime.now().isoformat()
    }
    if details:
        log_entry.update(details)
    
    logger.warning(f"Exclusion: {json.dumps(log_entry)}")
    
    # Also write to the exclusion CSV log
    exclusion_log_path = get_exclusion_log_path()
    file_exists = os.path.exists(exclusion_log_path)
    
    with open(exclusion_log_path, mode='a', newline='') as f:
        import csv
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['Subject_ID', 'Exclusion_Reason', 'Mean_FD'])
        
        # Extract Mean_FD if present in details
        mean_fd = details.get('Mean_FD', '') if details else ''
        writer.writerow([subject_id, reason, mean_fd])

def log_error(message: str, exception: Optional[Exception] = None) -> None:
    """
    Log an error event.
    
    Args:
        message: The error message.
        exception: Optional exception object.
    """
    logger = logging.getLogger(__name__)
    log_entry = {
        "message": message,
        "timestamp": datetime.now().isoformat()
    }
    if exception:
        log_entry["exception_type"] = type(exception).__name__
        log_entry["exception_message"] = str(exception)
    
    logger.error(f"Error: {json.dumps(log_entry)}")
    
    # Write to error log file
    error_log_path = get_error_log_path()
    with open(error_log_path, mode='a') as f:
        f.write(json.dumps(log_entry) + "\n")

def log_warning(message: str) -> None:
    """
    Log a warning event.
    
    Args:
        message: The warning message.
    """
    logger = logging.getLogger(__name__)
    logger.warning(message)