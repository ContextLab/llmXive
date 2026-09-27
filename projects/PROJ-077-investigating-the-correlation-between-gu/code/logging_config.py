"""
Logging Configuration Module.
Sets up logging infrastructure for the pipeline to record provenance and warnings.
"""
import logging
import os
import sys
from pathlib import Path
from config import ensure_directories

# Singleton logger instance
_logger = None

def get_logger(name: str = "llmXive_pipeline") -> logging.Logger:
    """Returns the configured logger instance."""
    global _logger
    if _logger is None:
        _logger = logging.getLogger(name)
        # Prevent adding handlers if already configured (e.g., in tests)
        if not _logger.handlers:
            _logger.setLevel(logging.INFO)
            
            # Console handler
            ch = logging.StreamHandler(sys.stdout)
            ch.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            ch.setFormatter(formatter)
            _logger.addHandler(ch)
            
            # File handler (provenance.log)
            ensure_directories()
            log_file = Path("data/processed/provenance.log")
            # Ensure the directory exists before creating the file handler
            log_file.parent.mkdir(parents=True, exist_ok=True)
            fh = logging.FileHandler(log_file)
            fh.setLevel(logging.INFO)
            fh.setFormatter(formatter)
            _logger.addHandler(fh)
    
    return _logger

def log_provenance(message: str):
    """Logs a provenance message for data lineage tracking."""
    logger = get_logger()
    logger.info(f"[PROVENANCE] {message}")

def log_warning(message: str):
    """Logs a warning message (e.g., zero variance detection, missing data)."""
    logger = get_logger()
    logger.warning(f"[WARNING] {message}")

def log_imputation_strategy(message: str):
    """Logs the imputation strategy used for missing values."""
    logger = get_logger()
    logger.info(f"[IMPUTATION] {message}")

def log_data_filtering(message: str):
    """Logs details about data filtering steps (e.g., null removal)."""
    logger = get_logger()
    logger.info(f"[FILTERING] {message}")

def log_pipeline_start():
    """Logs the start of the pipeline execution."""
    logger = get_logger()
    logger.info("Pipeline started.")

def log_pipeline_end():
    """Logs the successful completion of the pipeline execution."""
    logger = get_logger()
    logger.info("Pipeline finished.")