"""
Standardized logging utilities for the pipeline.
"""
import logging
import sys
from pathlib import Path
from typing import Optional
import os

_loggers = {}

def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Get a logger instance, creating it if necessary.
    """
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid adding handlers multiple times if called repeatedly
    if not logger.handlers:
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    _loggers[name] = logger
    return logger

def setup_file_logging(log_file: Path, level: int = logging.INFO) -> logging.Handler:
    """
    Set up a file handler for a specific logger or the root logger.
    """
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    return file_handler

def init_pipeline_logging(config: Optional[dict] = None):
    """
    Initialize logging for the entire pipeline based on config.
    """
    if config:
        level_str = config.get("logging", {}).get("level", "INFO")
        level = getattr(logging, level_str.upper(), logging.INFO)
        log_dir = Path(config.get("paths", {}).get("logs_dir", "logs"))
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / "pipeline.log"
        
        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        
        # Add file handler
        file_handler = setup_file_logging(log_file, level)
        root_logger.addHandler(file_handler)
        
        # Add console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    else:
        # Default setup
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        if not root_logger.handlers:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)
