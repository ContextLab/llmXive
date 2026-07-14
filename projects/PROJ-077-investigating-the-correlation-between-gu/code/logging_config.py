"""
Logging Configuration Module.
Sets up logging infrastructure for the pipeline.
"""
import logging
import os
from pathlib import Path
from config import ensure_directories

# Singleton logger instance
_logger = None

def get_logger(name: str = "llmXive_pipeline") -> logging.Logger:
    """Returns the configured logger instance."""
    global _logger
    if _logger is None:
        _logger = logging.getLogger(name)
        if not _logger.handlers:
            _logger.setLevel(logging.INFO)
            
            # Console handler
            ch = logging.StreamHandler()
            ch.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            ch.setFormatter(formatter)
            _logger.addHandler(ch)
            
            # File handler (provenance.log)
            ensure_directories()
            log_file = Path("data/processed/provenance.log")
            fh = logging.FileHandler(log_file)
            fh.setLevel(logging.INFO)
            fh.setFormatter(formatter)
            _logger.addHandler(fh)
    
    return _logger

def log_provenance(message: str):
    logger = get_logger()
    logger.info(f"[PROVENANCE] {message}")

def log_warning(message: str):
    logger = get_logger()
    logger.warning(f"[WARNING] {message}")

def log_imputation_strategy(message: str):
    logger = get_logger()
    logger.info(f"[IMPUTATION] {message}")

def log_data_filtering(message: str):
    logger = get_logger()
    logger.info(f"[FILTERING] {message}")

def log_pipeline_start():
    logger = get_logger()
    logger.info("Pipeline started.")

def log_pipeline_end():
    logger = get_logger()
    logger.info("Pipeline finished.")
