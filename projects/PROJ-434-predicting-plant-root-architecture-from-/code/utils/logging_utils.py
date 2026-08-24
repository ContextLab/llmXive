"""
Logging utilities for the pipeline.
"""
import os
import logging
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

def setup_logging(log_file: Optional[Path] = None, level: int = logging.INFO) -> logging.Logger:
    """Set up logging configuration."""
    logger = logging.getLogger("pipeline")
    logger.setLevel(level)

    # Clear existing handlers
    logger.handlers.clear()

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File handler (if specified)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_file)
        fh.setLevel(level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger

def get_logger(name: str = "pipeline") -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)

def log_excluded_record(logger: logging.Logger, record_id: str, reason_code: str):
    """Log an excluded record."""
    logger.info(f"Excluded record {record_id}: {reason_code}")

def log_species_exclusion_summary(logger: logging.Logger, species_list: List[str], reason: str):
    """Log a summary of excluded species."""
    logger.info(f"Excluded species ({reason}): {', '.join(species_list)}")

def log_validation_failure(logger: logging.Logger, message: str):
    """Log a validation failure."""
    logger.error(f"Validation Failed: {message}")
