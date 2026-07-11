"""
Logging infrastructure for the social exclusion prosociality project.

Provides a deterministic logging setup that writes structured JSON logs
to data/processed/mapping_log.json as required by the pipeline.
"""
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

# Ensure the processed directory exists
PROCESSED_DIR = Path("data/processed")
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = PROCESSED_DIR / "mapping_log.json"

class JSONLogHandler(logging.Handler):
    """
    Custom logging handler that writes log records as JSON objects
    to a specified file. Ensures deterministic output format.
    """
    def __init__(self, log_path: Path):
        super().__init__()
        self.log_path = log_path
        # Initialize file with empty list if it doesn't exist
        if not self.log_path.exists():
            with open(self.log_path, 'w', encoding='utf-8') as f:
                json.dump([], f)

    def emit(self, record: logging.LogRecord) -> None:
        try:
            # Create a deterministic log entry
            log_entry = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno
            }

            # Add extra fields if present
            if hasattr(record, 'mapping_info'):
                log_entry['mapping_info'] = record.mapping_info
            if hasattr(record, 'dataset_id'):
                log_entry['dataset_id'] = record.dataset_id
            if hasattr(record, 'raw_condition'):
                log_entry['raw_condition'] = record.raw_condition
            if hasattr(record, 'binary_condition'):
                log_entry['binary_condition'] = record.binary_condition

            # Read existing logs, append new entry, write back
            try:
                with open(self.log_path, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                logs = []

            logs.append(log_entry)

            with open(self.log_path, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=2, sort_keys=True)

        except Exception:
            # Fallback to stderr if file writing fails
            self.handleError(record)

def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
    logger_name: str = "social_exclusion"
) -> logging.Logger:
    """
    Configure the project logger with deterministic JSON output.
    
    Args:
        level: Logging level (default: INFO)
        log_file: Path to log file (default: data/processed/mapping_log.json)
        logger_name: Name of the logger to configure
        
    Returns:
        Configured logger instance
    """
    if log_file is None:
        log_file = LOG_FILE
    
    # Ensure directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Get or create logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    
    # Clear existing handlers to avoid duplicates
    if logger.handlers:
        logger.handlers.clear()
    
    # Add JSON file handler
    json_handler = JSONLogHandler(log_file)
    json_handler.setLevel(level)
    
    # Add console handler for visibility during development
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    
    logger.addHandler(json_handler)
    logger.addHandler(console_handler)
    
    return logger

def log_mapping(
    logger: logging.Logger,
    dataset_id: str,
    raw_condition: str,
    binary_condition: int,
    message: Optional[str] = None
) -> None:
    """
    Log a condition mapping event with structured data.
    
    Args:
        logger: The logger instance to use
        dataset_id: Identifier for the dataset
        raw_condition: Original condition string from raw data
        binary_condition: Mapped binary condition (0=control, 1=treatment)
        message: Optional descriptive message
    """
    extra = {
        'dataset_id': dataset_id,
        'raw_condition': raw_condition,
        'binary_condition': binary_condition
    }
    
    log_msg = message or f"Mapped '{raw_condition}' -> {binary_condition} for {dataset_id}"
    logger.info(log_msg, extra=extra)

# Convenience function for quick setup
def get_project_logger() -> logging.Logger:
    """
    Get the pre-configured project logger.
    
    Returns:
        Configured logger instance
    """
    return setup_logging()
