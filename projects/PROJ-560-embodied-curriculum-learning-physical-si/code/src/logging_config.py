import logging
import os
import sys
from pathlib import Path
from typing import Optional
import json

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
SKIPPED_LOG_PATH = Path("data/derivation_logs/skipped_records.log")

def setup_logging(log_file: Optional[str] = None) -> logging.Logger:
    """
    Configure logging for the application.
    
    Sets up a default file handler for skipped records log and a console handler.
    
    Args:
        log_file: Optional path to a general log file. If None, only the skipped_records.log is configured.
        
    Returns:
        The root logger.
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers to avoid duplicates
    if logger.handlers:
        logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(LOG_FORMAT)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Skipped records log handler (JSONL) - Always configured
    SKIPPED_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    skipped_handler = logging.FileHandler(SKIPPED_LOG_PATH, mode='a', encoding='utf-8')
    skipped_handler.setLevel(logging.WARNING)
    skipped_handler.setFormatter(logging.Formatter('%(message)s'))
    # We will manually write JSONL for skipped records, so this handler is just for structure
    # Actually, let's make this handler write JSONL for specific events if needed, 
    # but the main log_skipped_record function writes directly.
    # We add it to ensure the file exists and is ready.
    logger.addHandler(skipped_handler)
    
    # General log file if provided
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path, mode='a', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def write_skipped_record_jsonl(entry: dict) -> None:
    """
    Write a single entry to the skipped records log in JSONL format.
    
    Args:
        entry: Dictionary containing the log entry data.
    """
    SKIPPED_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SKIPPED_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")