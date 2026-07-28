import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd

from src.utils.logger import get_module_logger
from src.ingest.ocr_fallback import extract_psd_from_image
from src.exceptions import InsufficientDataError

logger = get_module_logger(__name__)

def read_row_count(file_path: Path) -> int:
    """
    Reads the row count from a parquet or json file.
    For parquet, uses pandas. For json, checks if it's a list or has a 'count' key.
    """
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return 0

    suffix = file_path.suffix.lower()
    
    if suffix == '.parquet':
        try:
            df = pd.read_parquet(file_path)
            return len(df)
        except Exception as e:
            logger.error(f"Error reading parquet file {file_path}: {e}")
            return 0
    elif suffix == '.json':
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            if isinstance(data, list):
                return len(data)
            elif isinstance(data, dict) and 'count' in data:
                return data['count']
            else:
                return 0
        except Exception as e:
            logger.error(f"Error reading json file {file_path}: {e}")
            return 0
    else:
        logger.warning(f"Unsupported file format for row count: {suffix}")
        return 0

def load_flagged_entries() -> List[Dict[str, Any]]:
    """Loads flagged entries from data/flagged_psd.json"""
    path = Path("data/flagged_psd.json")
    if not path.exists():
        return []
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load flagged entries: {e}")
        return []

def trigger_ocr_fallback(config: Dict[str, Any]) -> None:
    """
    Triggers OCR fallback for flagged entries if enabled in config.
    """
    if not config.get('ocr_enabled', False):
        logger.info("OCR fallback disabled in config.")
        return

    flagged = load_flagged_entries()
    if not flagged:
        logger.info("No flagged entries to process.")
        return

    logger.info(f"Processing {len(flagged)} flagged entries via OCR.")
    for entry in flagged:
        try:
            # Assuming entry has image_path and experiment_id
            extracted = extract_psd_from_image(
                image_path=entry.get('image_path'),
                flagged_entry_id=entry.get('experiment_id'),
                config=config
            )
            if extracted:
                logger.info(f"Successfully extracted data for {entry.get('experiment_id')}")
            else:
                logger.warning(f"OCR extraction failed for {entry.get('experiment_id')}")
        except Exception as e:
            logger.error(f"Error processing flagged entry {entry.get('experiment_id')}: {e}")

def check_size_gate(file_path: Optional[Path] = None) -> bool:
    """
    Checks the row count of the merged dataset (pre-processing).
    If count < 150, logs a CRITICAL warning but does NOT halt.
    This is T015c.
    
    If file_path is provided, it checks that specific file.
    Otherwise, defaults to the merged dataset path.
    """
    if file_path is None:
        file_path = Path("data/raw/merged_dataset.parquet")
    
    count = read_row_count(file_path)
    logger.info(f"Current dataset size: {count} rows")
    
    if count < 150:
        logger.critical(f"Dataset size < 150 experiments ({count}) (minimum viable) per spec SC-004. Proceeding with warning.")
        return False
    else:
        logger.info(f"Dataset size {count} meets minimum threshold.")
        return True

def check_processed_size(file_path: Optional[Path] = None) -> bool:
    """
    Checks the row count of the processed dataset (post-processing).
    If count < 150, raises SystemExit(1).
    This is T017c.
    """
    if file_path is None:
        file_path = Path("data/processed/ball_milling_dataset.parquet")
    
    count = read_row_count(file_path)
    logger.info(f"Processed dataset size: {count} rows")
    
    if count < 150:
        logger.critical(f"Processed dataset size < 150 experiments ({count}) (minimum viable) per spec SC-004")
        raise SystemExit(1)
    
    return True
