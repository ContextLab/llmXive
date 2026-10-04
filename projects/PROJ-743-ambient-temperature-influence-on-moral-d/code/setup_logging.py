import logging
import sys
from pathlib import Path
import os

def setup_logging(name: str, log_file: str = None, level: int = logging.INFO) -> logging.Logger:
    """
    Setup a logger with console and optional file handler.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if logger.handlers:
        return logger

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File handler (if specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_file)
        fh.setLevel(level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger

def get_data_quality_logger() -> logging.Logger:
    """
    Returns a pre-configured logger for data quality logs.
    """
    return setup_logging("data_quality", log_file="results/logs/data_quality_log.txt")
