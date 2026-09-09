import logging
import sys
from pathlib import Path
from typing import Optional
import json
from config import get_project_root, is_debug_mode

# Global logger summary storage
_log_summaries = []

def get_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """
    Configure and return a logger with consistent formatting.
    """
    if level is None:
        level = logging.DEBUG if is_debug_mode() else logging.INFO

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding handlers multiple times
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger

def log_missing_geometric_data(molecule_id: str, missing_fields: list) -> None:
    """
    Log a warning when geometric data is missing for a molecule.
    """
    logger = get_logger(__name__)
    msg = f"Missing geometric data for molecule {molecule_id}: {missing_fields}"
    logger.warning(msg)
    _log_summaries.append({"type": "warning", "message": msg})

def log_metallic_outlier(molecule_id: str, band_gap: float) -> None:
    """
    Log a warning when a metallic outlier (zero/negative band gap) is detected.
    """
    logger = get_logger(__name__)
    msg = f"Metallic outlier detected for molecule {molecule_id}: band_gap={band_gap} eV"
    logger.warning(msg)
    _log_summaries.append({"type": "warning", "message": msg})

def log_feature_extraction_error(molecule_id: str, error_msg: str) -> None:
    """
    Log an error when feature extraction fails.
    """
    logger = get_logger(__name__)
    msg = f"Feature extraction failed for molecule {molecule_id}: {error_msg}"
    logger.error(msg)
    _log_summaries.append({"type": "error", "message": msg})

def get_log_summary() -> list:
    """
    Return the list of log summaries captured during the run.
    """
    return _log_summaries

def save_log_summary(output_path: Optional[str] = None) -> None:
    """
    Save the log summary to a JSON file.
    """
    if output_path is None:
        root = get_project_root()
        output_path = str(root / "data" / "validation" / "log_summary.json")
    
    with open(output_path, 'w') as f:
        json.dump(_log_summaries, f, indent=2)
    
    _log_summaries.clear()
