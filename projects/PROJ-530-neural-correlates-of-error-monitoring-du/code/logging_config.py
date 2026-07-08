"""
Logging Configuration Module

Provides centralized logging setup and utility functions for the
research pipeline.
"""

import logging
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# Global logger instance
_logger = None

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance with the project's configured format.
    
    Args:
        name: Logger name. If None, returns the root logger.
                
    Returns:
        Configured logger instance.
    """
    global _logger
    
    if _logger is None:
        # Initialize with default settings if not already done
        initialize_logging()
    
    if name is None:
        return _logger
    else:
        return logging.getLogger(name)

def initialize_logging(log_file: Optional[str] = None, level: int = logging.INFO, console: bool = True) -> None:
    """
    Initialize the logging system with file and console handlers.
    
    Args:
        log_file: Path to the log file. If None, defaults to 'data/preprocessing.log'.
        level: Logging level.
        console: Whether to log to console.
    """
    global _logger
    
    # Create logger
    _logger = logging.getLogger("llmXive")
    _logger.setLevel(level)
    
    # Clear existing handlers
    _logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler
    if log_file is None:
        log_file = "data/preprocessing.log"
    
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    _logger.addHandler(file_handler)
    
    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        _logger.addHandler(console_handler)

def log_step(step_name: str, message: str) -> None:
    """
    Log a pipeline step.
    
    Args:
        step_name: Name of the step.
        message: Description of what is happening.
    """
    logger = get_logger()
    logger.info(f"[STEP: {step_name}] {message}")

def log_preprocessing_parameter(param_name: str, param_value: Any, unit: Optional[str] = None) -> None:
    """
    Log a preprocessing parameter.
    
    Args:
        param_name: Name of the parameter.
        param_value: Value of the parameter.
        unit: Optional unit of measurement.
    """
    logger = get_logger()
    value_str = f"{param_value} {unit}" if unit else str(param_value)
    logger.info(f"[PARAM] {param_name} = {value_str}")

def log_artifact(artifact_type: str, artifact_path: str, description: Optional[str] = None) -> None:
    """
    Log the creation of an artifact.
    
    Args:
        artifact_type: Type of artifact (e.g., 'epoch', 'model', 'figure').
        artifact_path: Path to the artifact file.
        description: Optional description.
    """
    logger = get_logger()
    msg = f"[ARTIFACT] {artifact_type.upper()}: {artifact_path}"
    if description:
        msg += f" - {description}"
    logger.info(msg)