"""
Logging utilities for the llmXive BES pipeline.

Provides functions to log experiment entries and general log messages.
"""
import logging
import os
import sys
from pathlib import Path
from typing import Optional
import json
from datetime import datetime

def setup_logging(log_file: str = "data/processed/experiment.log"):
    """
    Configure logging to write JSON entries to a file.
    
    Args:
        log_file: Path to the log file.
    """
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create a custom JSON formatter
    class JSONFormatter(logging.Formatter):
        def format(self, record):
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "level": record.levelname,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno
            }
            # Add extra fields if present
            if hasattr(record, 'cpu_percent'):
                log_entry["cpu_percent"] = record.cpu_percent
            if hasattr(record, 'wall_clock_time'):
                log_entry["wall_clock_time"] = record.wall_clock_time
            
            return json.dumps(log_entry)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Remove existing handlers to avoid duplicates
    root_logger.handlers = []
    
    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(file_handler)
    
    # Console handler for important messages
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    root_logger.addHandler(console_handler)

def log(message: str, level: str = "INFO", **kwargs):
    """
    Log a message with optional extra fields.
    
    Args:
        message: The log message.
        level: Log level (INFO, WARNING, ERROR, etc.).
        **kwargs: Extra fields to include in the log entry.
    """
    logger = logging.getLogger()
    log_record = logger.makeRecord(
        logger.name, 
        getattr(logging, level), 
        "", 
        0, 
        message, 
        (), 
        None
    )
    # Add extra fields
    for key, value in kwargs.items():
        setattr(log_record, key, value)
    logger.handle(log_record)

def log_experiment_entry(experiment_id: str, config: dict):
    """
    Log the start of an experiment.
    
    Args:
        experiment_id: Unique identifier for the experiment.
        config: Configuration dictionary for the experiment.
    """
    log(
        f"Experiment started: {experiment_id}",
        level="INFO",
        experiment_id=experiment_id,
        config_summary={k: v for k, v in config.items() if k != 'seed'} # Avoid logging seed directly if sensitive
    )