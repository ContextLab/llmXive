"""
Logging utilities for the project.
Provides specialized loggers for main events, exclusions, fallbacks, and methodology notes.
"""
import logging
import sys
import os
from typing import Optional, TextIO
from datetime import datetime

# Project Root
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
LOG_DIR = os.path.join(PROJECT_ROOT, "results", "logs")

# Ensure log directory exists
os.makedirs(LOG_DIR, exist_ok=True)

# Logger names
MAIN_LOGGER_NAME = "llmXive.main"
EXCLUSION_LOGGER_NAME = "llmXive.exclusion"
FALLBACK_LOGGER_NAME = "llmXive.fallback"
METHODOLOGY_LOGGER_NAME = "llmXive.methodology"

def get_main_logger() -> logging.Logger:
    return _get_logger(MAIN_LOGGER_NAME, os.path.join(LOG_DIR, "main.log"))

def get_exclusion_logger() -> logging.Logger:
    return _get_logger(EXCLUSION_LOGGER_NAME, os.path.join(LOG_DIR, "exclusion.log"))

def get_fallback_logger() -> logging.Logger:
    return _get_logger(FALLBACK_LOGGER_NAME, os.path.join(LOG_DIR, "fallback.log"))

def get_methodology_logger() -> logging.Logger:
    return _get_logger(METHODOLOGY_LOGGER_NAME, os.path.join(LOG_DIR, "methodology.log"))

def _get_logger(name: str, log_file: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Avoid duplicate handlers
    if not logger.handlers:
        # File handler
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.INFO)
        
        # Console handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        logger.addHandler(fh)
        logger.addHandler(ch)
    
    return logger

def log_exclusion(message: str, logger: Optional[logging.Logger] = None) -> None:
    if logger is None:
        logger = get_exclusion_logger()
    logger.warning(f"EXCLUSION: {message}")

def log_fallback_event(message: str, logger: Optional[logging.Logger] = None) -> None:
    if logger is None:
        logger = get_fallback_logger()
    logger.warning(f"FALLBACK: {message}")

def log_methodological_note(message: str, logger: Optional[logging.Logger] = None) -> None:
    if logger is None:
        logger = get_methodology_logger()
    logger.info(f"METHODOLOGY NOTE: {message}")

def log_pipeline_step(message: str, logger: Optional[logging.Logger] = None) -> None:
    if logger is None:
        logger = get_main_logger()
    logger.info(f"PIPELINE STEP: {message}")

def init_logging() -> None:
    """Initializes all loggers and ensures log directory exists."""
    get_main_logger()
    get_exclusion_logger()
    get_fallback_logger()
    get_methodology_logger()