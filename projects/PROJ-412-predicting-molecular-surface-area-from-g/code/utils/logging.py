import logging
import json
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
from .config import get_project_root

# Global logger instance
_logger: Optional[logging.Logger] = None
_setup_done = False

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent

def setup_logging(log_level: int = logging.INFO) -> None:
    """Setup logging configuration for the project."""
    global _logger, _setup_done
    
    if _setup_done:
        return
    
    project_root = get_project_root()
    logs_dir = project_root / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers
    root_logger.handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_format)
    root_logger.addHandler(console_handler)
    
    # File handler for general logs
    general_log_file = logs_dir / "pipeline.log"
    file_handler = logging.FileHandler(general_log_file)
    file_handler.setLevel(log_level)
    file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_format)
    root_logger.addHandler(file_handler)
    
    # File handler for excluded molecules (JSON format)
    excluded_log_file = logs_dir / "excluded_molecules.log"
    excluded_handler = logging.FileHandler(excluded_log_file)
    excluded_handler.setLevel(logging.WARNING)
    excluded_handler.setFormatter(logging.Formatter('%(message)s'))
    root_logger.addHandler(excluded_handler)
    
    # File handler for ingestion errors
    error_log_file = logs_dir / "ingestion_errors.log"
    error_handler = logging.FileHandler(error_log_file)
    error_handler.setLevel(logging.WARNING)
    error_handler.setFormatter(logging.Formatter('%(message)s'))
    root_logger.addHandler(error_handler)
    
    _logger = root_logger
    _setup_done = True

def get_logger(name: str = __name__) -> logging.Logger:
    """Get a logger instance."""
    if not _setup_done:
        setup_logging()
    return logging.getLogger(name)

def get_logger_level() -> int:
    """Get the current logger level."""
    if not _setup_done:
        setup_logging()
    return logging.getLogger().getEffectiveLevel()

def log_excluded_molecules(count: int, smiles_list: List[str]) -> None:
    """
    Log excluded molecules to logs/excluded_molecules.log in JSON format.
    
    Args:
        count: Number of excluded molecules
        smiles_list: List of SMILES strings that were excluded
    """
    if not _setup_done:
        setup_logging()
    
    logger = logging.getLogger(__name__)
    
    # Create a JSON log entry
    log_entry = {
        "type": "excluded_molecules",
        "count": count,
        "reason": "atom_count > 100",
        "smiles": smiles_list
    }
    
    # Log as JSON string
    logger.warning(json.dumps(log_entry))

def log_errors(errors: List[Exception]) -> None:
    """
    Log errors to logs/ingestion_errors.log.
    Invalid SMILES are logged at WARNING level.
    
    Args:
        errors: List of exceptions to log
    """
    if not _setup_done:
        setup_logging()
    
    logger = logging.getLogger(__name__)
    
    for error in errors:
        # Log invalid SMILES at WARNING level
        log_entry = {
            "type": "ingestion_error",
            "error_type": type(error).__name__,
            "message": str(error)
        }
        logger.warning(json.dumps(log_entry))

def log_dataset_statistics(stats: Dict[str, Any]) -> None:
    """
    Log dataset statistics.
    
    Args:
        stats: Dictionary containing dataset statistics
    """
    if not _setup_done:
        setup_logging()
    
    logger = logging.getLogger(__name__)
    logger.info(json.dumps({"type": "dataset_stats", **stats}))

def log_split_statistics(stats: Dict[str, Any]) -> None:
    """
    Log split statistics.
    
    Args:
        stats: Dictionary containing split statistics
    """
    if not _setup_done:
        setup_logging()
    
    logger = logging.getLogger(__name__)
    logger.info(json.dumps({"type": "split_stats", **stats}))

if __name__ == "__main__":
    setup_logging()
    logger = get_logger()
    logger.info("Logging module initialized")
    
    # Test logging functions
    log_excluded_molecules(2, ["CCO", "CCCO"])
    log_errors([ValueError("Invalid SMILES: CCOO"), ValueError("Invalid SMILES: CC")])
