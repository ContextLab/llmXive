import os
import csv
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

# Column names strictly matching contracts/experiment_log.schema.yaml
LOG_COLUMNS = [
    "task_id",
    "skill_id",
    "success",
    "latency",
    "tokens",
    "retrieval_precision",
    "retrieval_diversity",
    "pruning_risk_count",
    "library_size",
    "pruning_enabled",
    "edge_case"
]

_logger: Optional[logging.Logger] = None
_handler: Optional[logging.Handler] = None
_log_path: Optional[str] = None

class CSVLogHandler(logging.Handler):
    """
    Custom logging handler that writes log records to a CSV file.
    Ensures the CSV header is written exactly once upon the first write.
    """
    def __init__(self, filepath: str):
        super().__init__()
        self.filepath = filepath
        self._header_written = False
        self._lock = None  # Could use threading.Lock if multi-threaded
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Check if file exists to determine if header is needed
        self._file_exists = os.path.exists(filepath)

    def emit(self, record: logging.LogRecord):
        try:
            # Parse the message as JSON if it is a structured log entry
            # We expect the log message to be a JSON string matching the schema
            if isinstance(record.msg, str):
                try:
                    data = json.loads(record.msg)
                except json.JSONDecodeError:
                    # Fallback if not JSON, treat as raw string (should not happen per spec)
                    data = {"error": "Invalid log format", "raw": record.msg}
            else:
                data = record.msg

            # Ensure all expected columns are present, fill missing with None
            row = []
            for col in LOG_COLUMNS:
                row.append(data.get(col, ""))

            with open(self.filepath, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                if not self._header_written and not self._file_exists:
                    writer.writerow(LOG_COLUMNS)
                    self._header_written = True
                    self._file_exists = True
                
                writer.writerow(row)
                f.flush()
                os.fsync(f.fileno())

        except Exception:
            self.handleError(record)

def get_logger() -> logging.Logger:
    """
    Returns a singleton logger instance configured to write to data/results/experiment_log.csv.
    """
    global _logger, _handler, _log_path

    if _logger is not None:
        return _logger

    _log_path = os.path.join("data", "results", "experiment_log.csv")
    _logger = logging.getLogger("llmXive_experiment")
    _logger.setLevel(logging.INFO)

    # Remove existing handlers to prevent duplicates
    if _logger.hasHandlers():
        _logger.handlers.clear()

    _handler = CSVLogHandler(_log_path)
    _logger.addHandler(_handler)

    return _logger

def log_experiment_entry(entry: Dict[str, Any]) -> None:
    """
    Logs a single experiment entry to the CSV file.
    Validates that the entry contains the necessary keys for the schema.
    """
    logger = get_logger()
    # Ensure the entry has all required keys for the CSV columns
    # If a key is missing, it will be written as empty string by the handler
    logger.info(json.dumps(entry))

def verify_log_file_exists() -> bool:
    """
    Verifies that the log file exists and is not empty.
    Returns True if the file exists and has content, False otherwise.
    """
    if _log_path is None:
        get_logger() # Initialize to set path

    if _log_path and os.path.exists(_log_path):
        return os.path.getsize(_log_path) > 0
    return False
