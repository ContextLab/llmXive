"""
Logging configuration module for the llmXive Virtual Tactile Zero-Shot Adaptation project.

This module provides centralized logging setup with specific file paths, formats,
and loggers for different components of the pipeline (training, evaluation, etc.).
"""
import os
import sys
import logging
import logging.handlers
from pathlib import Path
from typing import Optional, Dict, Any

# Project root directory (relative to this file's location)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOGS_DIR = PROJECT_ROOT / "state" / "logs"

# Ensure logs directory exists
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Log format string
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Specific file paths for different loggers
LOG_FILE_PATHS = {
    "training": "training.log",
    "evaluation": "evaluation.log",
    "aggregation": "aggregation.log",
    "analysis": "analysis.log",
    "benchmark": "benchmark.log",
    "general": "general.log",
}

def get_logger(
    name: str,
    level: int = logging.INFO,
    log_to_file: bool = True,
    log_to_console: bool = True,
    log_file: Optional[str] = None,
) -> logging.Logger:
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name (usually __name__ of the module)
        level: Logging level (default: INFO)
        log_to_file: Whether to log to file (default: True)
        log_to_console: Whether to log to console (default: True)
        log_file: Optional specific log file name (default: None -> uses 'general.log')
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    
    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File handler
    if log_to_file:
        if log_file is None:
            log_file = LOG_FILE_PATHS["general"]
        
        log_path = LOGS_DIR / log_file
        
        # Ensure parent directories exist
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Use RotatingFileHandler for large logs
        file_handler = logging.handlers.RotatingFileHandler(
            log_path,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_logger_for_module(module_name: str) -> logging.Logger:
    """
    Get a logger for a specific module using its name.
    
    Args:
        module_name: The module name (e.g., 'train', 'evaluate')
    
    Returns:
        Configured logger instance
    """
    return get_logger(module_name, log_file=f"{module_name}.log")

def setup_training_logger() -> logging.Logger:
    """
    Set up and return the training logger.
    
    Returns:
        Configured training logger
    """
    return get_logger(
        "training",
        log_file=LOG_FILE_PATHS["training"],
        log_to_console=True,
        log_to_file=True,
    )

def setup_evaluation_logger() -> logging.Logger:
    """
    Set up and return the evaluation logger.
    
    Returns:
        Configured evaluation logger
    """
    return get_logger(
        "evaluation",
        log_file=LOG_FILE_PATHS["evaluation"],
        log_to_console=True,
        log_to_file=True,
    )

def setup_aggregation_logger() -> logging.Logger:
    """
    Set up and return the aggregation logger.
    
    Returns:
        Configured aggregation logger
    """
    return get_logger(
        "aggregation",
        log_file=LOG_FILE_PATHS["aggregation"],
        log_to_console=True,
        log_to_file=True,
    )

def setup_analysis_logger() -> logging.Logger:
    """
    Set up and return the analysis logger.
    
    Returns:
        Configured analysis logger
    """
    return get_logger(
        "analysis",
        log_file=LOG_FILE_PATHS["analysis"],
        log_to_console=True,
        log_to_file=True,
    )

def setup_benchmark_logger() -> logging.Logger:
    """
    Set up and return the benchmark logger.
    
    Returns:
        Configured benchmark logger
    """
    return get_logger(
        "benchmark",
        log_file=LOG_FILE_PATHS["benchmark"],
        log_to_console=True,
        log_to_file=True,
    )

def setup_all_loggers() -> Dict[str, logging.Logger]:
    """
    Set up all loggers and return them in a dictionary.
    
    Returns:
        Dictionary mapping logger names to logger instances
    """
    return {
        "training": setup_training_logger(),
        "evaluation": setup_evaluation_logger(),
        "aggregation": setup_aggregation_logger(),
        "analysis": setup_analysis_logger(),
        "benchmark": setup_benchmark_logger(),
    }

def init_logging() -> None:
    """
    Initialize logging for the entire project.
    
    This function sets up all loggers and ensures the logs directory exists.
    It should be called at the start of any main script.
    """
    # Ensure logs directory exists
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Set up all loggers
    setup_all_loggers()