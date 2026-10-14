"""
Centralized logging configuration for the research pipeline.
"""
import logging
import sys
from pathlib import Path
from config import RESULTS_LOG_DIR

def _get_base_logger(name: str, log_file: str = None):
    """Internal helper to configure loggers with consistent formatting."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Console handler for real-time visibility
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        
        if log_file:
            log_path = RESULTS_LOG_DIR / log_file
            log_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                fh = logging.FileHandler(log_path)
                fh.setFormatter(formatter)
                logger.addHandler(fh)
            except Exception as e:
                # Fallback to console if file writing fails
                print(f"Warning: Could not create log file {log_path}: {e}")
    
    return logger

def get_data_quality_logger():
    """Logger for data validation and quality gates."""
    return _get_base_logger("data_quality", "data_quality.log")

def get_exclusion_logger():
    """Logger for tracking records excluded from analysis."""
    return _get_base_logger("exclusion", "exclusion.log")

def get_model_diagnostics_logger():
    """Logger for model convergence and diagnostic output."""
    return _get_base_logger("model_diagnostics", "model_diagnostics.log")
