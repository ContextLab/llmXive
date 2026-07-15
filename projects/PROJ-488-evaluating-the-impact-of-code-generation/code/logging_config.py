import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

LOG_DIR = Path("logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Sets up a logger with console and file handlers.
    
    Args:
        name: Name of the logger.
        level: Logging level.
        
    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if logger.handlers:
        return logger
        
    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    # File handler
    log_file = LOG_DIR / f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    fh = logging.FileHandler(log_file)
    fh.setLevel(level)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """
    Gets or creates a logger.
    
    Args:
        name: Name of the logger.
        
    Returns:
        Logger instance.
    """
    return setup_logger(name)

def log_snippet_info(logger: logging.Logger, snippet_id: str, length: int):
    """
    Logs snippet information.
    
    Args:
        logger: Logger instance.
        snippet_id: ID of the snippet.
        length: Length of the snippet.
    """
    logger.info(f"Snippet {snippet_id} processed. Length: {length}")

def log_metric_extraction(logger: logging.Logger, metric_type: str, value: float):
    """
    Logs metric extraction.
    
    Args:
        logger: Logger instance.
        metric_type: Type of metric.
        value: Value of the metric.
    """
    logger.info(f"Metric {metric_type}: {value}")

def log_error(logger: logging.Logger, error_message: str):
    """
    Logs an error message.
    
    Args:
        logger: Logger instance.
        error_message: Error message.
    """
    logger.error(error_message)

def main():
    """
    Main entry point for logging configuration.
    """
    logger = get_logger("test_logger")
    log_snippet_info(logger, "test_1", 100)
    log_metric_extraction(logger, "complexity", 5.5)
    log_error(logger, "This is a test error.")

if __name__ == "__main__":
    main()
