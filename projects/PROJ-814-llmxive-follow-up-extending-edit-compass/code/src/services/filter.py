import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from src.utils.logging import get_logger, setup_logging

logger = get_logger(__name__)

TARGET_CATEGORIES = ["World Knowledge Reasoning", "Visual Reasoning"]
RAW_DATA_FILENAME = "edit_compass_metadata.json"
FILTERED_OUTPUT_FILENAME = "filtered_dataset.json"

def load_raw_data(raw_dir: Path) -> List[Dict[str, Any]]:
    """
    Load raw data from the data/raw directory.
    Raises FileNotFoundError if file missing, ValueError if malformed JSON.
    """
    file_path = raw_dir / RAW_DATA_FILENAME
    
    if not file_path.exists():
        raise FileNotFoundError(f"Raw data file not found at: {file_path}")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Malformed JSON in raw data file {file_path}: {e}") from e
    except Exception as e:
        raise RuntimeError(f"Failed to read raw data file: {e}") from e

    if isinstance(data, dict) and 'data' in data:
        data = data['data']

    if not isinstance(data, list):
        raise ValueError("Raw data must be a list of records or a dict with 'data' key containing a list.")

    return data

def filter_by_categories(data: List[Dict[str, Any]], categories: List[str]) -> List[Dict[str, Any]]:
    """
    Filter records by category.
    """
    filtered = [
        record for record in data
        if isinstance(record, dict) and record.get('category') in categories
    ]
    return filtered

def save_filtered_data(filtered_data: List[Dict[str, Any]], output_dir: Path) -> Path:
    """
    Save filtered data to JSON.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / FILTERED_OUTPUT_FILENAME

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(filtered_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Saved {len(filtered_data)} records to {output_path}")
    return output_path

def main():
    setup_logging()
    raw_dir = Path("data/raw")
    filtered_dir = Path("data/filtered")

    logger.info("Starting data filtering...")

    try:
        # 1. Load
        raw_data = load_raw_data(raw_dir)
        logger.info(f"Loaded {len(raw_data)} records from raw data.")

        # 2. Filter
        filtered_data = filter_by_categories(raw_data, TARGET_CATEGORIES)
        logger.info(f"Filtered to {len(filtered_data)} records for categories: {TARGET_CATEGORIES}")

        if len(filtered_data) == 0:
            raise ValueError(f"ERROR: Filter returned zero records for categories: {TARGET_CATEGORIES}")

        # 3. Save
        save_filtered_data(filtered_data, filtered_dir)
        logger.info("Filtering completed successfully.")

    except FileNotFoundError as e:
        logger.error(f"ERROR: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during filtering: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()