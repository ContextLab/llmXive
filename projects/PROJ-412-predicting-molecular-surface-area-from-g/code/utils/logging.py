import logging
import json
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
from .config import get_project_root

_logger_instance: Optional[logging.Logger] = None

def setup_logging(log_file: Optional[Path] = None, level: int = logging.INFO):
    """
    Configures the root logger for the project.
    
    Args:
        log_file: Optional path to a log file. If provided, logs are written to file.
        level: Logging level (e.g., logging.INFO, logging.DEBUG).
    """
    global _logger_instance
    
    # Prevent re-configuring if already set up
    if _logger_instance is not None and _logger_instance.hasHandlers():
        return

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_format)
    root_logger.addHandler(console_handler)

    # File handler (if requested)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_format)
        root_logger.addHandler(file_handler)

    _logger_instance = root_logger

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Retrieves or creates a logger with the given name.
    Ensures logging is set up first.
    """
    if _logger_instance is None:
        # Default setup if not explicitly called
        setup_logging()
    
    return logging.getLogger(name)

def get_logger_level(name: Optional[str] = None) -> int:
    """
    Returns the logging level of the specified logger.
    """
    logger = get_logger(name)
    return logger.level

def log_excluded_molecules(count: int, smiles_list: List[str]) -> None:
    """
    Logs excluded molecules to the excluded_molecules.log file.
    
    Args:
        count: Number of excluded molecules.
        smiles_list: List of SMILES strings that were excluded.
    """
    logger = get_logger(__name__)
    log_dir = get_project_root() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "excluded_molecules.log"
    
    with open(log_file, "a") as f:
        entry = {
            "count": count,
            "smiles": smiles_list
        }
        f.write(json.dumps(entry) + "\n")
    
    logger.info(f"Logged {count} excluded molecules to {log_file}")

def log_errors(errors: List[Exception]) -> None:
    """
    Logs errors to the ingestion_errors.log file.
    
    Args:
        errors: List of Exception objects.
    """
    logger = get_logger(__name__)
    log_dir = get_project_root() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "ingestion_errors.log"
    
    with open(log_file, "a") as f:
        for err in errors:
            entry = {
                "error_type": type(err).__name__,
                "message": str(err)
            }
            f.write(json.dumps(entry) + "\n")
    
    logger.info(f"Logged {len(errors)} errors to {log_file}")

def log_dataset_statistics(stats: Dict[str, Any]) -> None:
    """
    Logs dataset statistics to a generic stats log.
    
    Args:
        stats: Dictionary of statistics.
    """
    logger = get_logger(__name__)
    log_dir = get_project_root() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "dataset_stats.log"
    
    with open(log_file, "a") as f:
        f.write(json.dumps(stats) + "\n")
    
    logger.info(f"Logged dataset statistics to {log_file}")

def log_split_statistics(stats: Dict[str, Any]) -> None:
    """
    Logs split statistics to a generic stats log.
    
    Args:
        stats: Dictionary of split statistics.
    """
    logger = get_logger(__name__)
    log_dir = get_project_root() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "split_stats.log"
    
    with open(log_file, "a") as f:
        f.write(json.dumps(stats) + "\n")
    
    logger.info(f"Logged split statistics to {log_file}")
