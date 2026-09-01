import logging
import os
import sys
from pathlib import Path
from typing import Optional

def setup_logging(log_file: Optional[Path] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Configure logging for the research pipeline.
    
    Args:
        log_file: Optional path to log file. If None, logs to stdout only.
        level: Logging level (default: INFO)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger("llmXive")
    logger.setLevel(level)
    
    # Clear existing handlers
    logger.handlers = []
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
    return logger

def log(message: str, level: str = "INFO", logger: Optional[logging.Logger] = None):
    """
    Log a message at the specified level.
    
    Args:
        message: The message to log
        level: Log level string ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
        logger: Optional logger instance (uses default if None)
    """
    if logger is None:
        logger = logging.getLogger("llmXive")
        
    log_method = getattr(logger, level.lower(), logger.info)
    log_method(message)

def log_experiment_entry(experiment_id: str, params: dict, logger: Optional[logging.Logger] = None):
    """
    Log the start of an experiment with its parameters.
    
    Args:
        experiment_id: Unique identifier for the experiment
        params: Dictionary of experiment parameters
        logger: Optional logger instance
    """
    if logger is None:
        logger = logging.getLogger("llmXive")
        
    logger.info(f"Starting experiment: {experiment_id}")
    for key, value in params.items():
        logger.info(f"  {key}: {value}")
