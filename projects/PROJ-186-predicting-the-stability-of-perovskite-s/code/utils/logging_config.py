"""
Logging configuration for the perovskite stability prediction pipeline.
"""
import os
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


class PipelineFormatter(logging.Formatter):
    """Custom formatter for pipeline logs."""
    
    def format(self, record):
        # Add custom fields for pipeline events
        if hasattr(record, 'event_type'):
            record.msg = f"[{record.event_type}] {record.msg}"
        return super().format(record)


def get_logger(name: str = "pipeline") -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name (default: "pipeline")
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.DEBUG)
    
    # Create formatters
    detailed_formatter = PipelineFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(detailed_formatter)
    
    # File handler
    log_dir = Path(__file__).parent.parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "pipeline.log"
    
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10 MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger


def log_exclusion_reason(reason: str, formula: str, logger: Optional[logging.Logger] = None):
    """
    Log an exclusion reason for a data entry.
    
    Args:
        reason: The reason for exclusion
        formula: The chemical formula of the excluded entry
        logger: Logger instance (uses default if None)
    """
    if logger is None:
        logger = get_logger()
    
    logger.info(f"EXCLUSION: [{reason}] [{formula}]", extra={'event_type': 'EXCLUSION'})


def log_pipeline_event(event_name: str, details: Optional[dict] = None, 
                     logger: Optional[logging.Logger] = None):
    """
    Log a pipeline event with optional details.
    
    Args:
        event_name: Name of the event
        details: Optional dictionary of event details
        logger: Logger instance (uses default if None)
    """
    if logger is None:
        logger = get_logger()
    
    msg = event_name
    if details:
        msg += f" - {details}"
    
    logger.info(msg, extra={'event_type': 'EVENT'})


def initialize_logging():
    """
    Initialize logging for the entire pipeline.
    This should be called once at the start of any pipeline script.
    """
    # Ensure log directory exists
    log_dir = Path(__file__).parent.parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # Set root logger level
    logging.root.setLevel(logging.DEBUG)
    
    # Add file handler to root if not present
    if not logging.root.handlers:
        log_file = log_dir / "pipeline.log"
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,
            backupCount=5
        )
        file_handler.setFormatter(PipelineFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        logging.root.addHandler(file_handler)
