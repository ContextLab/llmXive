import logging
import os
from pathlib import Path
from typing import Optional
import json
from datetime import datetime

# Ensure logs directory exists
LOGS_DIR = Path(__file__).parent.parent.parent / "data" / "results"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

def get_logger(name: str) -> logging.Logger:
    """Returns a configured logger instance."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    # File handler
    log_file = LOGS_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.INFO)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger

def log_exclusion_count(count: int, reason: str) -> None:
    """Logs exclusion statistics."""
    logger = get_logger(__name__)
    logger.info(f"Excluded {count} records: {reason}")

def log_sample_size(count: int) -> None:
    """Logs the final sample size."""
    logger = get_logger(__name__)
    logger.info(f"Final sample size: {count}")

def log_error_context(error: Exception, context: str = "") -> None:
    """Logs an error with context."""
    logger = get_logger(__name__)
    logger.error(f"{context}: {str(error)}", exc_info=True)
