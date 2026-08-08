import logging
import sys
import os
from typing import Optional, TextIO
from datetime import datetime

_loggers = {}

def get_main_logger(name: str = "main") -> logging.Logger:
    return _get_logger(name, "results/pipeline.log")

def get_exclusion_logger(name: str = "exclusion") -> logging.Logger:
    return _get_logger(name, "results/exclusion_report.log")

def get_fallback_logger(name: str = "fallback") -> logging.Logger:
    return _get_logger(name, "results/fallback_events.log")

def get_methodology_logger(name: str = "methodology") -> logging.Logger:
    return _get_logger(name, "results/methodology_notes.log")

def _get_logger(name: str, log_file: str) -> logging.Logger:
    if name in _loggers:
        return _loggers[name]
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    if not logger.handlers:
        # Ensure log directory exists
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.DEBUG)
        
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        logger.addHandler(fh)
        logger.addHandler(ch)
    
    _loggers[name] = logger
    return logger

def log_exclusion(logger: logging.Logger, reason: str, count: int) -> None:
    logger.info(f"Excluded {count} records: {reason}")

def log_fallback_event(logger: logging.Logger, event: str) -> None:
    logger.warning(f"Fallback triggered: {event}")

def log_methodological_note(logger: logging.Logger, note: str) -> None:
    logger.info(f"Methodological Note: {note}")

def log_pipeline_step(logger: logging.Logger, step: str) -> None:
    logger.info(f"Pipeline Step: {step}")

def init_logging():
    """Initialize logging configuration."""
    pass
