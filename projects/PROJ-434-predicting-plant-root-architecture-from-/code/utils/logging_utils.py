"""
Logging utilities for the pipeline.
"""
import os
import logging
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

def setup_logging(log_file: Optional[Path] = None, level: int = logging.INFO) -> None:
    """Configure root logger with console and file handlers."""
    if log_file is None:
        log_file = Path("data/logs/pipeline.log")
    
    # Ensure log directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger()
    logger.setLevel(level)

    # Clear existing handlers to avoid duplicates
    logger.handlers = []

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(level)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name."""
    return logging.getLogger(name)

def log_excluded_record(logger: logging.Logger, record_id: str, reason_code: str) -> None:
    """Log an excluded record."""
    logger.warning(f"Excluded record {record_id}: {reason_code}")

def log_species_exclusion_summary(logger: logging.Logger, species_name: str, count: int, reason: str) -> None:
    """Log species exclusion summary."""
    logger.info(f"Excluded species {species_name} (count={count}): {reason}")

def log_validation_failure(logger: logging.Logger, message: str) -> None:
    """Log a validation failure."""
    logger.error(f"Validation Failure: {message}")