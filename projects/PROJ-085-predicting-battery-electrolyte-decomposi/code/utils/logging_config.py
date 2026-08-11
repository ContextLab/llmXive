import logging
import sys
from pathlib import Path
from typing import Optional
import json
from config import get_project_root, is_debug_mode

# Configure logging
_logger_instance: Optional[logging.Logger] = None
_log_summary: list = []

def get_logger(name: str) -> logging.Logger:
    """
    Gets or creates a logger with consistent formatting.
    
    Args:
        name: Name of the logger (usually __name__)
    
    Returns:
        Configured logging.Logger instance
    """
    global _logger_instance
    
    if _logger_instance is None:
        _logger_instance = logging.getLogger("llmXive")
        _logger_instance.setLevel(logging.DEBUG if is_debug_mode() else logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG if is_debug_mode() else logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        
        if not _logger_instance.handlers:
            _logger_instance.addHandler(console_handler)
    
    return logging.getLogger(name)

def log_missing_geometric_data(molecule_id: str, missing_fields: list) -> None:
    """
    Logs a warning when geometric data is missing for a molecule.
    
    Args:
        molecule_id: The ID of the molecule
        missing_fields: List of missing field names
    """
    logger = get_logger(__name__)
    logger.warning(f"Missing geometric data for molecule {molecule_id}: {missing_fields}")
    _log_summary.append({
        "type": "missing_geometric_data",
        "molecule_id": molecule_id,
        "fields": missing_fields
    })

def log_metallic_outlier(molecule_id: str, gap_value: float) -> None:
    """
    Logs a warning when a metallic outlier (zero/negative gap) is detected.
    
    Args:
        molecule_id: The ID of the molecule
        gap_value: The calculated band gap
    """
    logger = get_logger(__name__)
    logger.warning(f"Metallic outlier detected for molecule {molecule_id}: band gap = {gap_value} eV")
    _log_summary.append({
        "type": "metallic_outlier",
        "molecule_id": molecule_id,
        "gap_value": gap_value
    })

def log_feature_extraction_error(molecule_id: str, error_msg: str) -> None:
    """
    Logs an error when feature extraction fails for a molecule.
    
    Args:
        molecule_id: The ID of the molecule
        error_msg: Description of the error
    """
    logger = get_logger(__name__)
    logger.error(f"Feature extraction failed for molecule {molecule_id}: {error_msg}")
    _log_summary.append({
        "type": "extraction_error",
        "molecule_id": molecule_id,
        "error": error_msg
    })

def get_log_summary() -> list:
    """Returns the summary of all logged warnings and errors."""
    return _log_summary.copy()

def save_log_summary(output_path: Optional[str] = None) -> None:
    """
    Saves the log summary to a JSON file.
    
    Args:
        output_path: Path to save the summary. Defaults to data/validation/log_summary.json
    """
    if output_path is None:
        output_path = str(get_project_root() / "data" / "validation" / "log_summary.json")
    
    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(_log_summary, f, indent=2)
    
    # Clear summary after saving
    _log_summary.clear()
