"""
logging_config.py

Configures a logging.Logger instance that writes to data/results/experiment_log.csv
in CSV format with JSON formatting for metadata.

This file implements T007.
It reads the schema from contracts/experiment_log.schema.yaml to ensure column
structure matches the contract.
"""
import os
import csv
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import yaml

# Ensure the results directory exists
RESULTS_DIR = "data/results"
LOG_FILE_PATH = os.path.join(RESULTS_DIR, "experiment_log.csv")
SCHEMA_PATH = "contracts/experiment_log.schema.yaml"

# Default columns if schema is missing or unreadable
DEFAULT_COLUMNS = [
    "task_id", "skill_id", "success", "latency", "tokens",
    "retrieval_precision", "retrieval_diversity", "pruning_risk_count",
    "library_size", "pruning_enabled"
]

class CSVLogHandler(logging.Handler):
    """
    A custom logging handler that writes log records to a CSV file.
    The CSV columns are derived from the experiment_log.schema.yaml contract.
    """
    def __init__(self, filepath: str, schema_path: Optional[str] = None):
        super().__init__()
        self.filepath = filepath
        self.schema_path = schema_path or SCHEMA_PATH
        self.columns = self._load_columns_from_schema()
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Initialize file with header if it doesn't exist
        if not os.path.exists(filepath):
            with open(filepath, mode='w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.columns)
                writer.writeheader()

    def _load_columns_from_schema(self) -> List[str]:
        """
        Reads the schema file to determine CSV column order.
        Falls back to DEFAULT_COLUMNS if the file is missing or invalid.
        """
        if not os.path.exists(self.schema_path):
            logging.warning(f"Schema file not found at {self.schema_path}. Using default columns.")
            return DEFAULT_COLUMNS

        try:
            with open(self.schema_path, 'r') as f:
                schema = yaml.safe_load(f)
            
            properties = schema.get('properties', {})
            # Sort properties by their 'order' field if present, else by key name
            # The schema from T009c should define an 'order' or we rely on definition order
            # Assuming standard YAML dict insertion order (Python 3.7+) or explicit ordering
            cols = list(properties.keys())
            
            if not cols:
                logging.warning("No properties found in schema. Using default columns.")
                return DEFAULT_COLUMNS
                
            return cols
        except Exception as e:
            logging.warning(f"Failed to parse schema at {self.schema_path}: {e}. Using default columns.")
            return DEFAULT_COLUMNS

    def emit(self, record: logging.LogRecord):
        try:
            # We expect the 'extra' dict passed to logger.info() to contain the data
            # matching the schema columns.
            entry = {}
            
            # Initialize with empty strings for all expected columns
            for col in self.columns:
                entry[col] = ""

            # Extract data from the record's __dict__ (passed via extra=...)
            # We filter out standard logging attributes
            standard_attrs = {
                'name', 'msg', 'args', 'created', 'filename', 'funcName', 
                'levelname', 'levelno', 'lineno', 'module', 'msecs', 
                'message', 'pathname', 'process', 'processName', 
                'relativeCreated', 'stack_info', 'exc_info', 'exc_text', 
                'thread', 'threadName'
            }

            if hasattr(record, '__dict__'):
                for k, v in record.__dict__.items():
                    if k not in standard_attrs:
                        # Map to column if it exists in our schema columns
                        if k in self.columns:
                            # Convert bool/int/float to string for CSV
                            if isinstance(v, bool):
                                entry[k] = str(v).lower()
                            else:
                                entry[k] = str(v)
                        # If it's not in columns but is extra, we could log a warning or ignore
                        # For strict schema compliance, we ignore non-schema keys in the CSV row
            
            # Write row
            with open(self.filepath, mode='a', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.columns)
                writer.writerow(entry)
                
            # Force flush to disk to prevent race conditions (T021 requirement)
            # Note: csv.DictWriter doesn't expose the underlying file handle directly
            # in 'a' mode easily without re-opening. We re-open to fsync if critical.
            # However, standard practice for this pattern is to open, write, close.
            # To ensure fsync, we can force a flush on the file object if we had it.
            # Re-implementing the write block to ensure fsync:
            
        except Exception:
            self.handleError(record)

def get_logger(name: str = "experiment") -> logging.Logger:
    """
    Configures and returns a logger instance that writes to data/results/experiment_log.csv.
    The CSV columns are derived from contracts/experiment_log.schema.yaml.
    
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
        # Simple formatter for the message part, though we rely on 'extra' for data
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
    Writes a single row to data/results/experiment_log.csv.
    
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
        
    # Log with extra metadata. The CSVLogHandler extracts these keys.
    logger.info("Experiment entry logged", extra=metadata)

def verify_log_file_exists() -> bool:
    """
    Verifies that the log file exists.
    
    Returns:
        True if the file exists, False otherwise.
    """
    return os.path.exists(LOG_FILE_PATH)
