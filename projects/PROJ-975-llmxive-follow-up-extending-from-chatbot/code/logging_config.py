import os
import csv
import json
import logging
from typing import Optional, Dict, Any, List
from llmxive_toolkit import get_logger as toolkit_get_logger, paths

# Column names strictly matching T005 requirement and contracts/experiment_log.schema.yaml
LOG_COLUMNS = [
    "run_id",
    "task_id",
    "library_size",
    "pruning_enabled",
    "success",
    "latency_ms",
    "tokens_used",
    "retrieval_precision",
    "retrieval_diversity",
    "edge_case"
]

_logger: Optional[logging.Logger] = None

class CSVLogHandler(logging.Handler):
    """
    Custom logging handler that writes log records to a CSV file.
    Ensures the CSV header is written exactly once upon the first write.
    """
    def __init__(self, filepath: str):
        super().__init__()
        self.filepath = filepath
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

    def emit(self, record: logging.LogRecord):
        try:
            # Parse the message as JSON if it is a structured log entry
            if isinstance(record.msg, str):
                try:
                    data = json.loads(record.msg)
                except json.JSONDecodeError:
                    data = {"error": "Invalid log format", "raw": record.msg}
            else:
                data = record.msg

            # Ensure all expected columns are present, fill missing with empty string
            row = []
            for col in LOG_COLUMNS:
                val = data.get(col, "")
                # Convert boolean to string 'true'/'false' for CSV consistency
                if isinstance(val, bool):
                    val = str(val).lower()
                row.append(val)

            file_exists = os.path.exists(self.filepath)
            is_empty = file_exists and os.path.getsize(self.filepath) == 0

            with open(self.filepath, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                # Write header if file doesn't exist or is empty
                if not file_exists or is_empty:
                    writer.writerow(LOG_COLUMNS)
                
                writer.writerow(row)
                f.flush()
                os.fsync(f.fileno())

        except Exception:
            self.handleError(record)

def get_logger(name: str = "llmXive_experiment") -> logging.Logger:
    """
    Returns a logger instance configured to write to data/results/experiment_log.csv.
    Uses llmxive_toolkit.get_logger for consistent formatting.
    """
    global _logger

    if _logger is not None:
        return _logger

    # Use platform helper for base logger
    _logger = toolkit_get_logger(name)
    _logger.setLevel(logging.INFO)

    # Add the CSV handler
    log_path = str(paths.data("results", "experiment_log.csv"))
    csv_handler = CSVLogHandler(log_path)
    _logger.addHandler(csv_handler)

    return _logger

def log_experiment_entry(entry: Dict[str, Any]) -> None:
    """
    Logs a single experiment entry to the CSV file.
    """
    logger = get_logger()
    # Pass as JSON string to be parsed by CSVLogHandler
    logger.info(json.dumps(entry))

def verify_log_file_exists() -> bool:
    """
    Verifies that the log file exists and is not empty.
    """
    log_path = paths.data("results", "experiment_log.csv")
    if log_path.exists():
        return log_path.stat().st_size > 0
    return False
