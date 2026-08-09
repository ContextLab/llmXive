"""
Logging utilities for the project.
Provides centralized logging configuration and helper functions.
"""
import logging
import json
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

from .config import get_project_root

# Global logger instance
_logger: Optional[logging.Logger] = None

def setup_logging(log_level: int = logging.INFO, log_file: Optional[str] = None) -> logging.Logger:
    """
    Setup the root logger for the project.
    
    Args:
        log_level: Logging level (default: INFO)
        log_file: Optional path to log file. If None, logs to console only.
    
    Returns:
        logging.Logger: The configured root logger
    """
    global _logger
    
    if _logger is not None:
        return _logger
    
    _logger = logging.getLogger("llmXive")
    _logger.setLevel(log_level)
    
    # Prevent duplicate handlers
    if _logger.handlers:
        _logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_format)
    _logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        project_root = get_project_root()
        log_path = project_root / log_file
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(log_level)
        file_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_format)
        _logger.addHandler(file_handler)
    
    return _logger

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance for the project.
    
    Args:
        name: Optional name for the logger (creates a child logger)
    
    Returns:
        logging.Logger: Logger instance
    """
    if _logger is None:
        setup_logging()
    
    if name:
        return _logger.getChild(name)
    return _logger

def get_logger_level(name: Optional[str] = None) -> int:
    """
    Get the logging level for a specific logger.
    
    Args:
        name: Optional name for the logger
    
    Returns:
        int: The logging level
    """
    logger = get_logger(name)
    return logger.level

def log_excluded_molecules(count: int, smiles_list: List[str]) -> None:
    """
    Log information about excluded molecules.
    
    Args:
        count: Number of excluded molecules
        smiles_list: List of SMILES strings for excluded molecules
    """
    logger = get_logger(__name__)
    if count > 0:
        logger.warning(f"Excluded {count} molecules due to filter criteria")
        # Log first few for debugging
        if smiles_list:
            logger.debug(f"Sample excluded SMILES: {smiles_list[:5]}")
    
    # Also write to a dedicated log file for audit trail
    project_root = get_project_root()
    log_file = project_root / "logs" / "excluded_molecules.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_file, "a", encoding="utf-8") as f:
        entry = {
            "count": count,
            "timestamp": logging.Formatter("%Y-%m-%d %H:%M:%S").format(logging.LogRecord("", 0, "", 0, "", (), None)),
            "smiles_sample": smiles_list[:10] if len(smiles_list) > 10 else smiles_list
        }
        f.write(json.dumps(entry) + "\n")

def log_errors(errors: List[Exception]) -> None:
    """
    Log a list of exceptions to the error log file.
    
    Args:
        errors: List of exception objects
    """
    logger = get_logger(__name__)
    
    project_root = get_project_root()
    log_file = project_root / "logs" / "ingestion_errors.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_file, "a", encoding="utf-8") as f:
        for error in errors:
            entry = {
                "error_type": type(error).__name__,
                "message": str(error),
                "timestamp": logging.Formatter("%Y-%m-%d %H:%M:%S").format(logging.LogRecord("", 0, "", 0, "", (), None))
            }
            f.write(json.dumps(entry) + "\n")
            logger.error(f"Error: {type(error).__name__}: {error}")

def log_dataset_statistics(stats: Dict[str, Any]) -> None:
    """
    Log dataset statistics.
    
    Args:
        stats: Dictionary containing dataset statistics
    """
    logger = get_logger(__name__)
    logger.info(f"Dataset statistics: {json.dumps(stats, indent=2)}")

def log_split_statistics(split_stats: Dict[str, Any]) -> None:
    """
    Log data split statistics.
    
    Args:
        split_stats: Dictionary containing split statistics
    """
    logger = get_logger(__name__)
    logger.info(f"Split statistics: {json.dumps(split_stats, indent=2)}")
