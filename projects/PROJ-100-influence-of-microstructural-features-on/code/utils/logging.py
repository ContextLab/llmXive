"""
Logging utilities for the pipeline.
Provides standardized loggers for exclusions, fallbacks, methodology, and main pipeline steps.
"""
import logging
import sys
import os
from typing import Optional, TextIO
from datetime import datetime

LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "results")
os.makedirs(LOG_DIR, exist_ok=True)

def get_main_logger(name: str = "pipeline") -> logging.Logger:
    """Returns the main logger for general pipeline steps."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # File handler for main log
    file_handler = logging.FileHandler(os.path.join(LOG_DIR, "main_pipeline.log"))
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

def get_exclusion_logger() -> logging.Logger:
    """Returns a logger specifically for data exclusion events."""
    logger = logging.getLogger("exclusion")
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)
    file_handler = logging.FileHandler(os.path.join(LOG_DIR, "exclusion_report.log"))
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger

def get_fallback_logger() -> logging.Logger:
    """Returns a logger for fallback events (e.g., synthetic data generation)."""
    logger = logging.getLogger("fallback")
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.WARNING)
    file_handler = logging.FileHandler(os.path.join(LOG_DIR, "fallback_events.log"))
    file_handler.setLevel(logging.WARNING)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger

def get_methodology_logger() -> logging.Logger:
    """Returns a logger for methodological notes and disclaimers."""
    logger = logging.getLogger("methodology")
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)
    file_handler = logging.FileHandler(os.path.join(LOG_DIR, "methodology_notes.log"))
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger

def log_exclusion(message: str) -> None:
    """Logs an exclusion event."""
    get_exclusion_logger().info(message)

def log_fallback_event(message: str) -> None:
    """Logs a fallback event."""
    get_fallback_logger().warning(message)

def log_methodological_note(message: str) -> None:
    """Logs a methodological note."""
    get_methodology_logger().info(message)

def log_pipeline_step(step_name: str) -> None:
    """Logs a pipeline step."""
    get_main_logger().info(f"Step: {step_name}")

def init_logging():
    """Initializes all loggers."""
    get_main_logger()
    get_exclusion_logger()
    get_fallback_logger()
    get_methodology_logger()