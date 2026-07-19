import logging
import os
from pathlib import Path
from typing import Optional
import json
from datetime import datetime

from .config import DATA_RESULTS_DIR

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    # File handler
    log_file = DATA_RESULTS_DIR / "ingestion.log"
    if not DATA_RESULTS_DIR.exists():
        DATA_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.INFO)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    
    return logger

def log_exclusion_count(category: str, count: int):
    """Logs exclusion counts to the log file and a summary JSON."""
    logger = get_logger("ingestion")
    logger.info(f"Excluded {count} records due to: {category}")
    
    # Update summary file
    summary_file = DATA_RESULTS_DIR / "exclusion_summary.json"
    summary = {}
    if summary_file.exists():
        with open(summary_file, 'r') as f:
            summary = json.load(f)
    
    summary[category] = count
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)

def log_sample_size(n: int):
    logger = get_logger("ingestion")
    logger.info(f"Current sample size: N={n}")

def log_error_context(error_type: str, message: str):
    logger = get_logger("ingestion")
    logger.error(f"{error_type}: {message}")