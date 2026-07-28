"""
Size Gate Utility.
Handles row count checks and warnings/halts based on dataset size.
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from src.utils.logger import get_module_logger
from src.exceptions import InsufficientDataError

logger = get_module_logger(__name__)


def read_row_count(count_file_path: Optional[str] = None) -> int:
    """
    Reads the row count from the row_count.json file.
    
    Args:
        count_file_path: Path to row_count.json. Defaults to data/processed/row_count.json.
        
    Returns:
        int: The row count.
        
    Raises:
        FileNotFoundError: If the count file does not exist.
        ValueError: If the count is not an integer.
    """
    if count_file_path is None:
        # Default path based on project structure
        count_file_path = "data/processed/row_count.json"
    
    path = Path(count_file_path)
    if not path.exists():
        raise FileNotFoundError(f"Row count file not found: {path}")
    
    with open(path, 'r') as f:
        data = json.load(f)
        
    if 'count' not in data:
        raise ValueError("Row count file does not contain 'count' key.")
        
    return int(data['count'])


def load_flagged_entries(flagged_file_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Loads flagged entries from data/flagged_psd.json.
    
    Args:
        flagged_file_path: Path to flagged_psd.json.
        
    Returns:
        List of flagged entries.
    """
    if flagged_file_path is None:
        flagged_file_path = "data/flagged_psd.json"
        
    path = Path(flagged_file_path)
    if not path.exists():
        logger.warning(f"Flagged entries file not found: {path}. Returning empty list.")
        return []
        
    with open(path, 'r') as f:
        return json.load(f)


def trigger_ocr_fallback(flagged_entries: List[Dict[str, Any]], config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Triggers OCR fallback for flagged entries if config allows.
    
    Args:
        flagged_entries: List of flagged entries.
        config: Configuration dictionary.
        
    Returns:
        Updated list of entries (with extracted data if OCR succeeded).
    """
    if not flagged_entries:
        return []
        
    # This function would call the OCR extraction logic defined in T014c
    # For now, we just log that it would happen.
    logger.info(f"Triggering OCR fallback for {len(flagged_entries)} flagged entries.")
    # In a real implementation, this would iterate and call extract_psd_from_image
    return flagged_entries


def check_size_gate(count_file_path: Optional[str] = None) -> bool:
    """
    Checks the dataset size gate (Warning only - T015c).
    
    Reads the row count and logs a critical warning if < 150.
    Does NOT halt execution (does not raise SystemExit).
    
    Args:
        count_file_path: Path to row_count.json.
        
    Returns:
        bool: True if count >= 150, False otherwise.
    """
    try:
        count = read_row_count(count_file_path)
    except FileNotFoundError as e:
        logger.error(f"Cannot check size gate: {e}")
        return False
        
    if count < 150:
        logger.critical(f"Size Gate Warning: Dataset size is {count} rows, which is less than the minimum viable threshold of 150.")
        return False
    else:
        logger.info(f"Size Gate Check passed: Dataset size is {count} rows.")
        return True
