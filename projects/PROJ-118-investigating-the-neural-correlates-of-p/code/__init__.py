"""
llmXive Research Pipeline: Code Package
========================================

This package contains the core implementation for the auditory oddball EEG analysis.
It provides utility functions for logging, path resolution, and configuration loading.

Exports:
    - setup_logging: Configures the project's logging infrastructure.
    - get_project_root: Returns the absolute path to the project root.
    - get_data_path: Resolves paths relative to data directories.
    - load_config: Loads the YAML configuration file.
"""

import logging
import os
from pathlib import Path
from typing import Optional

# Import config loading utility to make it available at package level
from .config_utils import load_config

__version__ = "0.1.0"
__all__ = [
    "setup_logging",
    "get_project_root",
    "get_data_path",
    "get_processed_path",
    "get_raw_path",
    "load_config",
]

# Define project root relative to this file's location (project root is parent of 'code')
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

def get_project_root() -> Path:
    """
    Returns the absolute Path to the project root directory.
    
    Returns:
        Path: The project root directory.
    """
    return _PROJECT_ROOT

def get_raw_path(subpath: Optional[str] = None) -> Path:
    """
    Returns the absolute Path to the data/raw directory.
    
    Args:
        subpath (Optional[str]): Optional relative subpath within data/raw.
    
    Returns:
        Path: The resolved path to data/raw or a subdirectory.
    """
    base = _PROJECT_ROOT / "data" / "raw"
    if subpath:
        return base / subpath
    return base

def get_processed_path(subpath: Optional[str] = None) -> Path:
    """
    Returns the absolute Path to the data/processed directory.
    
    Args:
        subpath (Optional[str]): Optional relative subpath within data/processed.
    
    Returns:
        Path: The resolved path to data/processed or a subdirectory.
    """
    base = _PROJECT_ROOT / "data" / "processed"
    if subpath:
        return base / subpath
    return base

def get_data_path(subpath: Optional[str] = None) -> Path:
    """
    Generic helper to resolve paths relative to the data root.
    
    Args:
        subpath (Optional[str]): Relative path segments.
    
    Returns:
        Path: Resolved path.
    """
    base = _PROJECT_ROOT / "data"
    if subpath:
        return base / subpath
    return base

def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    module_name: Optional[str] = None
) -> logging.Logger:
    """
    Configures the logging infrastructure for the pipeline.
    
    Sets up a console handler and optionally a file handler.
    Uses a consistent format including timestamp, level, and message.
    
    Args:
        level (int): Logging level (e.g., logging.DEBUG, logging.INFO).
        log_file (Optional[str]): Path to a log file. If None, no file handler is added.
        module_name (Optional[str]): Name for the logger. Defaults to 'llmXive_pipeline'.
    
    Returns:
        logging.Logger: The configured logger instance.
    """
    logger_name = module_name or "llmXive_pipeline"
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    
    # Prevent adding duplicate handlers if called multiple times
    if logger.handlers:
        return logger
    
    # Define format
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File Handler (optional)
    if log_file:
        # Ensure directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger