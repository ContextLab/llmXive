import logging
import sys
from pathlib import Path
from typing import Optional
import json
from config import get_project_root, is_debug_mode

# Global logger instance
_logger: Optional[logging.Logger] = None

def get_logger(name: str = "battery_decomposition") -> logging.Logger:
    """
    Configure and return a project-specific logger.
    
    Sets up logging to both console and a file within the project's logs directory.
    The log level is determined by the DEBUG_MODE environment variable or config.
    
    Args:
        name: The name for the logger (usually __name__ of the caller).
        
    Returns:
        A configured logging.Logger instance.
    """
    global _logger
    
    if _logger is not None and _logger.name == name:
        return _logger
    
    # Initialize logger
    logger = logging.getLogger(name)
    
    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        logger.handlers.clear()
    
    # Determine log level
    log_level = logging.DEBUG if is_debug_mode() else logging.INFO
    logger.setLevel(log_level)
    
    # Create project root and logs directory
    project_root = get_project_root()
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # Formatter with timestamp and level
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler
    log_file = logs_dir / f"{name}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    _logger = logger
    return logger

def log_missing_geometric_data(molecule_id: str, missing_fields: list) -> None:
    """
    Log a warning when geometric data is missing for a molecule.
    
    Args:
        molecule_id: The unique identifier for the molecule.
        missing_fields: List of field names that were missing.
    """
    logger = get_logger()
    msg = f"Missing geometric data for molecule {molecule_id}: {missing_fields}"
    logger.warning(msg)

def log_metallic_outlier(molecule_id: str, band_gap: float) -> None:
    """
    Log a warning when a molecule exhibits metallic behavior (zero or negative band gap).
    
    Args:
        molecule_id: The unique identifier for the molecule.
        band_gap: The calculated band gap value.
    """
    logger = get_logger()
    msg = f"Metallic behavior outlier detected for molecule {molecule_id}: band_gap = {band_gap} eV"
    logger.warning(msg)

def log_feature_extraction_error(molecule_id: str, error: Exception) -> None:
    """
    Log an error when feature extraction fails for a molecule.
    
    Args:
        molecule_id: The unique identifier for the molecule.
        error: The exception that was raised.
    """
    logger = get_logger()
    msg = f"Feature extraction failed for molecule {molecule_id}: {str(error)}"
    logger.error(msg, exc_info=True)

def get_log_summary() -> dict:
    """
    Generate a summary of log statistics (count by level).
    
    Returns:
        A dictionary with counts of log messages by level.
    """
    logger = get_logger()
    summary = {
        "DEBUG": 0,
        "INFO": 0,
        "WARNING": 0,
        "ERROR": 0,
        "CRITICAL": 0
    }
    
    # We cannot directly count handlers' internal buffers, 
    # so we return a static summary structure for integration with external tools.
    # In a real production system, a custom handler would track counts.
    # For now, this ensures the interface exists.
    return summary

def save_log_summary(output_path: Optional[str] = None) -> str:
    """
    Save the current log summary to a JSON file.
    
    Args:
        output_path: Optional path to save the summary. If None, saves to logs/log_summary.json.
        
    Returns:
        The path where the summary was saved.
    """
    summary = get_log_summary()
    project_root = get_project_root()
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    if output_path is None:
        output_path = str(logs_dir / "log_summary.json")
    
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    return output_path