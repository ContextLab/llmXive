"""
Logging infrastructure for the cognitive decline prediction pipeline.

Configures loggers to capture excluded subjects and feature-filtering logs.
"""
import logging
import os
from pathlib import Path
from typing import Optional
from config import LOG_DIR, LOG_LEVEL

# Ensure log directory exists
if LOG_DIR:
    LOG_DIR.mkdir(parents=True, exist_ok=True)

# Global logger configuration
_loggers = {}

def setup_logger(name: str, log_file: Optional[str] = None, level: int = LOG_LEVEL) -> logging.Logger:
    """
    Setup a logger with file and console handlers.
    
    Args:
        name: Logger name.
        log_file: Optional filename for log output.
        level: Logging level.
    
    Returns:
        Configured logger instance.
    """
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid adding handlers multiple times if called repeatedly
    if logger.handlers:
        _loggers[name] = logger
        return logger

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File handler (optional)
    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setLevel(level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    _loggers[name] = logger
    return logger

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance by name.
    
    Args:
        name: Logger name.
    
    Returns:
        Logger instance.
    """
    return setup_logger(name)

def log_excluded_subjects(subject_ids: list, reason: str, log_file: Optional[str] = None):
    """
    Log excluded subjects to a specific file or the main log.
    
    Args:
        subject_ids: List of excluded subject IDs.
        reason: Reason for exclusion.
        log_file: Optional specific log file path.
    """
    logger = get_logger("excluded_subjects")
    if log_file:
        # Ensure file handler exists
        if not any(isinstance(h, logging.FileHandler) and h.baseFilename == str(log_file) 
                   for h in logger.handlers):
            fh = logging.FileHandler(log_file)
            fh.setLevel(logging.INFO)
            fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            logger.addHandler(fh)
    
    logger.info(f"Excluded {len(subject_ids)} subjects: {reason}")
    for sid in subject_ids:
        logger.info(f"  - {sid}")

def log_feature_filtering(feature_name: str, reason: str, log_file: Optional[str] = None):
    """
    Log feature filtering events.
    
    Args:
        feature_name: Name of the filtered feature.
        reason: Reason for filtering.
        log_file: Optional specific log file path.
    """
    logger = get_logger("feature_filtering")
    if log_file:
        if not any(isinstance(h, logging.FileHandler) and h.baseFilename == str(log_file) 
                   for h in logger.handlers):
            fh = logging.FileHandler(log_file)
            fh.setLevel(logging.INFO)
            fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            logger.addHandler(fh)
    
    logger.info(f"Filtered feature '{feature_name}': {reason}")