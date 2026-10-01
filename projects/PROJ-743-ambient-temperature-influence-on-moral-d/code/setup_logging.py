"""
Logging infrastructure setup.
"""
import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from config import get_path_env_override

def ensure_directories():
    """Ensure logging directories exist."""
    dirs = [
        "results/logs",
        "results/figures",
        "results/stats"
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)

def setup_logging():
    """Configure root logging."""
    ensure_directories()
    log_file = Path("results/logs/pipeline.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

def get_data_quality_logger(name: str = "data_quality") -> logging.Logger:
    """Get a logger specifically for data quality checks."""
    ensure_directories()
    logger = logging.getLogger(name)
    if not logger.handlers:
        log_file = Path("results/logs/data_quality.log")
        handler = logging.FileHandler(log_file)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

def get_model_diagnostics_logger(name: str = "model_diagnostics") -> logging.Logger:
    """Get a logger for model diagnostics."""
    ensure_directories()
    logger = logging.getLogger(name)
    if not logger.handlers:
        log_file = Path("results/logs/model_diagnostics.log")
        handler = logging.FileHandler(log_file)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

def get_exclusion_logger(name: str = "exclusions") -> logging.Logger:
    """Get a logger for excluded records."""
    ensure_directories()
    logger = logging.getLogger(name)
    if not logger.handlers:
        log_file = Path("results/logs/exclusions.log")
        handler = logging.FileHandler(log_file)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

def main():
    setup_logging()