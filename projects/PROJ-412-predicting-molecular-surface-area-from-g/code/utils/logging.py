import logging
import json
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
from .config import get_project_root

_logger_instance: Optional[logging.Logger] = None

def setup_logging(log_level: int = logging.INFO, log_file: Optional[str] = None) -> logging.Logger:
    """
    Setup the root logger for the project.
    
    Args:
        log_level: The logging level (e.g., logging.INFO).
        log_file: Optional path to a log file.
        
    Returns:
        logging.Logger: The configured logger.
    """
    global _logger_instance
    if _logger_instance is not None:
        return _logger_instance

    logger = logging.getLogger("llmXive")
    logger.setLevel(log_level)

    if not logger.handlers:
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_format)
        logger.addHandler(console_handler)

        # File handler (optional)
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
            logger.addHandler(file_handler)

    _logger_instance = logger
    return logger

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Args:
        name: The name of the logger.
        
    Returns:
        logging.Logger: The logger instance.
    """
    if _logger_instance is None:
        setup_logging()
    return logging.getLogger(f"llmXive.{name}")

def get_logger_level(level_str: str) -> int:
    """
    Convert a string level to a logging constant.
    
    Args:
        level_str: String representation of the level (e.g., 'INFO').
        
    Returns:
        int: The logging level constant.
    """
    levels = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL,
    }
    return levels.get(level_str.upper(), logging.INFO)

def log_excluded_molecules(count: int, smiles_list: List[str]) -> None:
    """
    Log excluded molecules to the logs/excluded_molecules.log file.
    
    Args:
        count: Number of excluded molecules.
        smiles_list: List of SMILES strings for excluded molecules.
    """
    logger = get_logger("data_ingestion")
    logger.info(f"Excluded {count} molecules due to filtering criteria.")
    if smiles_list:
        logger.warning(f"Excluded SMILES: {smiles_list}")

def log_errors(errors: List[Exception]) -> None:
    """
    Log errors to the logs/ingestion_errors.log file.
    Invalid SMILES are logged at WARNING level.
    
    Args:
        errors: List of exception objects to log.
    """
    logger = get_logger("data_ingestion")
    for error in errors:
        error_str = str(error).lower()
        if "invalid" in error_str or "smiles" in error_str:
            logger.warning(f"Invalid SMILES detected: {error}")
        else:
            logger.error(f"Error occurred: {error}")

def log_dataset_statistics(stats: Dict[str, Any]) -> None:
    """
    Log dataset statistics.
    
    Args:
        stats: Dictionary containing dataset statistics.
    """
    logger = get_logger("data_ingestion")
    logger.info(f"Dataset Statistics: {json.dumps(stats, indent=2)}")

def log_split_statistics(stats: Dict[str, Any]) -> None:
    """
    Log split statistics.
    
    Args:
        stats: Dictionary containing split statistics.
    """
    logger = get_logger("data_splitting")
    logger.info(f"Split Statistics: {json.dumps(stats, indent=2)}")