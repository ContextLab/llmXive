"""
logging_config.py

Configures a logging.Logger instance that writes to data/results/experiment_log.csv
in CSV format with JSON formatting for metadata.

This file implements T007.
"""
import os
import csv
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime

# Ensure the results directory exists
RESULTS_DIR = "data/results"
LOG_FILE_PATH = os.path.join(RESULTS_DIR, "experiment_log.csv")

class CSVLogHandler(logging.Handler):
    """
    A custom logging handler that writes log records to a CSV file.
    Metadata is stored as a JSON string in a specific column.
    """
    def __init__(self, filepath: str):
        super().__init__()
        self.filepath = filepath
        self.fieldnames = [
            "timestamp", "level", "message", "metadata_json"
        ]
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Initialize file with header if it doesn't exist
        if not os.path.exists(filepath):
            with open(filepath, mode='w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.fieldnames)
                writer.writeheader()

    def emit(self, record: logging.LogRecord):
        try:
            # Prepare the log entry
            entry = {
                "timestamp": datetime.now().isoformat(),
                "level": record.levelname,
                "message": record.getMessage(),
                "metadata_json": ""
            }

            # Extract extra metadata if present and convert to JSON
            if hasattr(record, '__dict__'):
                # Filter standard logging attributes to keep only extras
                extras = {k: v for k, v in record.__dict__.items() 
                          if k not in ['name', 'msg', 'args', 'created', 'filename', 
                                       'funcName', 'levelname', 'levelno', 'lineno', 
                                       'module', 'msecs', 'message', 'pathname', 
                                       'process', 'processName', 'relativeCreated', 
                                       'stack_info', 'exc_info', 'exc_text', 'thread', 
                                       'threadName']}
                if extras:
                    entry["metadata_json"] = json.dumps(extras)

            # Append to CSV
            with open(self.filepath, mode='a', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.fieldnames)
                writer.writerow(entry)
        except Exception:
            self.handleError(record)

def get_logger(name: str = "experiment") -> logging.Logger:
    """
    Configures and returns a logger instance that writes to data/results/experiment_log.csv.
    
    Args:
        name: Name for the logger instance.
        
    Returns:
        Configured logging.Logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Avoid adding duplicate handlers if called multiple times
    if not logger.handlers:
        handler = CSVLogHandler(LOG_FILE_PATH)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    return logger

def log_experiment_entry(
    task_id: str, 
    success: bool, 
    latency: float, 
    tokens: int, 
    retrieval_precision: float, 
    retrieval_diversity: float, 
    pruning_risk_count: int, 
    library_size: int, 
    pruning_enabled: bool,
    extra_metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Convenience function to log a structured experiment entry.
    
    Args:
        task_id: Identifier for the task.
        success: Boolean indicating task success.
        latency: Execution latency in seconds.
        tokens: Number of tokens used.
        retrieval_precision: Calculated retrieval precision.
        retrieval_diversity: Calculated retrieval diversity.
        pruning_risk_count: Count of pruned high-similarity skills.
        library_size: Current library size.
        pruning_enabled: Whether pruning was active.
        extra_metadata: Additional dictionary of metadata to include.
    """
    logger = get_logger()
    
    metadata = {
        "task_id": task_id,
        "success": success,
        "latency": latency,
        "tokens": tokens,
        "retrieval_precision": retrieval_precision,
        "retrieval_diversity": retrieval_diversity,
        "pruning_risk_count": pruning_risk_count,
        "library_size": library_size,
        "pruning_enabled": pruning_enabled
    }
    
    if extra_metadata:
        metadata.update(extra_metadata)
        
    # Log with extra metadata
    logger.info(f"Experiment run completed for task {task_id}", extra=metadata)

def verify_log_file_exists() -> bool:
    """
    Verifies that the log file exists.
    
    Returns:
        True if the file exists, False otherwise.
    """
    return os.path.exists(LOG_FILE_PATH)
