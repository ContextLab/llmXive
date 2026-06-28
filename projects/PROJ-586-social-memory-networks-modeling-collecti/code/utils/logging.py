"""
Logging utilities for social memory network experiments.

This module provides centralized logging with timestamps to experiment.log
for tracking experiment progress, errors, and results.
"""

import logging
import os
from pathlib import Path
from typing import Optional, Union
from datetime import datetime
import threading

# Thread-local storage for loggers
_logger_lock = threading.Lock()
_loggers: dict = {}

def setup_logger(
    name: str,
    log_file: Optional[str] = None,
    level: int = logging.INFO
) -> logging.Logger:
    """
    Set up a logger with file and console handlers.
    
    Args:
        name: Logger name
        log_file: Path to log file (optional)
        level: Logging level
    
    Returns:
        Configured logger instance
    """
    with _logger_lock:
        if name in _loggers:
            return _loggers[name]
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatter with timestamp
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler if log_file specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    with _logger_lock:
        _loggers[name] = logger
    
    return logger

def get_logger(name: str = __name__) -> logging.Logger:
    """
    Get or create a logger by name.
    
    Args:
        name: Logger name (default: module name)
    
    Returns:
        Logger instance
    """
    with _logger_lock:
        if name in _loggers:
            return _loggers[name]
    
    # Default logger setup
    return setup_logger(
        name=name,
        log_file="experiment.log",
        level=logging.INFO
    )

def log_experiment_start(
    num_games: int,
    num_agents: int,
    context_condition: str
) -> None:
    """
    Log experiment start with parameters.
    
    Args:
        num_games: Number of games to run
        num_agents: Number of agents
        context_condition: Context condition name
    """
    logger = get_logger("experiment")
    logger.info("=" * 60)
    logger.info("EXPERIMENT STARTED")
    logger.info("=" * 60)
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info(f"Number of games: {num_games}")
    logger.info(f"Number of agents: {num_agents}")
    logger.info(f"Context condition: {context_condition}")

def log_experiment_end(output_file: str) -> None:
    """
    Log experiment completion.
    
    Args:
        output_file: Path to output file
    """
    logger = get_logger("experiment")
    logger.info("=" * 60)
    logger.info("EXPERIMENT COMPLETED")
    logger.info("=" * 60)
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info(f"Output file: {output_file}")

def info(msg: str) -> None:
    """Log info message."""
    get_logger().info(msg)

def warning(msg: str) -> None:
    """Log warning message."""
    get_logger().warning(msg)

def error(msg: str) -> None:
    """Log error message."""
    get_logger().error(msg)

def debug(msg: str) -> None:
    """Log debug message."""
    get_logger().debug(msg)

def critical(msg: str) -> None:
    """Log critical message."""
    get_logger().critical(msg)

if __name__ == "__main__":
    # Test logging
    logger = get_logger("test")
    log_experiment_start(1000, 3, "full")
    logger.info("Test message")
    log_experiment_end("test_output.csv")
