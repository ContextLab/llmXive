"""
Logging configuration and utilities for the llmXive project.

This module provides centralized logging setup and retrieval functions
to ensure consistent logging across all project components.
"""
import logging
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
import json

# Project root
project_root = Path(__file__).parent.parent.parent
data_dir = project_root / "data"
raw_data_dir = data_dir / "raw"

# Ensure data directories exist
raw_data_dir.mkdir(parents=True, exist_ok=True)

# Global logger registry
_loggers = {}
_setup_complete = False

def setup_logging(
    log_level: int = logging.INFO,
    log_file: Optional[str] = None,
    console_output: bool = True
) -> None:
    """
    Configure the root logger for the project.
    
    Args:
        log_level: Logging level (e.g., logging.DEBUG, logging.INFO)
        log_file: Optional path to log file
        console_output: Whether to output to console
    """
    global _setup_complete
    
    if _setup_complete:
        return
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers
    root_logger.handlers = []
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # File handler (default to data/raw/)
    if log_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = str(raw_data_dir / f"experiment_{timestamp}.log")
    
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    file_handler = logging.FileHandler(log_path)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    _setup_complete = True
    logging.info(f"Logging configured: file={log_file}, level={log_level}")

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance by name.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Configured logger instance
    """
    if name not in _loggers:
        logger = logging.getLogger(name)
        if not logger.handlers:
            # Ensure logging is set up
            if not _setup_complete:
                setup_logging()
            logger.setLevel(logging.DEBUG)
        _loggers[name] = logger
    
    return _loggers[name]

def get_log_path() -> Path:
    """
    Get the default log directory path.
    
    Returns:
        Path to the log directory
    """
    return raw_data_dir

def export_log_summary(log_file: str, output_file: str) -> None:
    """
    Export a summary of log entries to a JSON file.
    
    Args:
        log_file: Path to the log file
        output_file: Path to output JSON file
    """
    log_path = Path(log_file)
    if not log_path.exists():
        raise FileNotFoundError(f"Log file not found: {log_file}")
    
    summary = {
        "file": str(log_file),
        "entries": [],
        "counts": {
            "DEBUG": 0,
            "INFO": 0,
            "WARNING": 0,
            "ERROR": 0,
            "CRITICAL": 0
        }
    }
    
    with open(log_path, 'r') as f:
        for line in f:
            if line.strip():
                summary["entries"].append(line.strip())
                for level in summary["counts"]:
                    if f" - {level} - " in line:
                        summary["counts"][level] += 1
                        break
    
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logging.info(f"Log summary exported to {output_file}")
