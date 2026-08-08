"""
Logging utilities for the project.
"""
import logging
import json
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

from .config import get_project_root

def setup_logging(log_file: str = None, level: int = logging.INFO) -> logging.Logger:
    """
    Sets up the root logger with console and file handlers.
    """
    logger = logging.getLogger()
    logger.setLevel(level)

    # Clear existing handlers
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger

def get_logger(name: str = None) -> logging.Logger:
    """
    Gets a logger instance, optionally setting up logging if not already done.
    """
    if name is None:
        name = "llmXive"
    logger = logging.getLogger(name)
    if not logger.handlers:
        # Setup default logging if no handlers exist
        setup_logging(level=logging.INFO)
    return logger

def get_logger_level(level_str: str) -> int:
    """Converts a string level to logging level."""
    levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    return levels.get(level_str.upper(), logging.INFO)

def log_excluded_molecules(count: int, smiles_list: List[str], logger: logging.Logger = None):
    """
    Logs excluded molecules to a JSON file and logger.
    """
    if logger is None:
        logger = get_logger()
    
    log_entry = {
        "type": "excluded_molecules",
        "count": count,
        "smiles_list": smiles_list
    }
    
    logger.warning(f"Excluded {count} molecules due to validation errors.")
    
    # Write to log file
    log_file = get_project_root() / "logs" / "excluded_molecules.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_file, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')

def log_errors(errors: List[Dict[str, Any]], logger: logging.Logger = None):
    """
    Logs ingestion errors to a JSON file and logger.
    """
    if logger is None:
        logger = get_logger()
    
    log_entry = {
        "type": "ingestion_errors",
        "errors": errors
    }
    
    logger.error(f"Logged {len(errors)} ingestion errors.")
    
    # Write to log file
    log_file = get_project_root() / "logs" / "ingestion_errors.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_file, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')

def log_dataset_statistics(stats: Dict[str, Any], logger: logging.Logger = None):
    """
    Logs dataset statistics.
    """
    if logger is None:
        logger = get_logger()
    
    logger.info(f"Dataset Statistics: {json.dumps(stats, indent=2)}")
    
    # Write to log file
    log_file = get_project_root() / "logs" / "dataset_statistics.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_file, 'w') as f:
        f.write(json.dumps(stats, indent=2))

def log_split_statistics(split_info: Dict[str, Any], logger: logging.Logger = None):
    """
    Logs split statistics.
    """
    if logger is None:
        logger = get_logger()
    
    logger.info(f"Split Statistics: {json.dumps(split_info, indent=2)}")
    
    # Write to log file
    log_file = get_project_root() / "logs" / "split_statistics.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_file, 'w') as f:
        f.write(json.dumps(split_info, indent=2))
