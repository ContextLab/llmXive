import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from src.utils.logging import get_logger, setup_logging

TARGET_CATEGORIES = ["World Knowledge Reasoning", "Visual Reasoning"]
RAW_DATA_DIR = Path("data/raw")
FILTERED_DATA_DIR = Path("data/filtered")
RAW_DATA_FILE = RAW_DATA_DIR / "edit_compass_dataset.json"
FILTERED_DATA_FILE = FILTERED_DATA_DIR / "filtered_dataset.json"

def load_raw_data(raw_file_path: Path) -> List[Dict[str, Any]]:
    """
    Load the raw dataset from a JSON file.

    Args:
        raw_file_path: Path to the raw JSON file.

    Returns:
        List of records from the dataset.

    Raises:
        FileNotFoundError: If the raw data file does not exist.
        ValueError: If the file is not valid JSON or not a list.
    """
    logger = get_logger(__name__)

    if not raw_file_path.exists():
        logger.error(f"Raw data file not found: {raw_file_path}")
        raise FileNotFoundError(f"Raw data file not found: {raw_file_path}")

    try:
        with open(raw_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in raw data file: {e}")
        raise ValueError(f"Invalid JSON in raw data file: {e}")

    if not isinstance(data, list):
        logger.error(f"Raw data must be a list of records, got {type(data)}")
        raise ValueError(f"Raw data must be a list of records, got {type(data)}")

    logger.info(f"Loaded {len(data)} records from {raw_file_path}")
    return data

def filter_by_categories(records: List[Dict[str, Any]], categories: List[str]) -> List[Dict[str, Any]]:
    """
    Filter records by the 'category' field.

    Args:
        records: List of dataset records.
        categories: List of target category strings to match exactly.

    Returns:
        List of records where 'category' is in the provided list.
    """
    logger = get_logger(__name__)
    logger.info(f"Filtering records for categories: {categories}")

    filtered = [
        record for record in records
        if record.get("category") in categories
    ]

    logger.info(f"Filtered from {len(records)} to {len(filtered)} records")
    return filtered

def save_filtered_data(records: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save the filtered records to a JSON file.

    Args:
        records: List of filtered records.
        output_path: Path to the output JSON file.
    """
    logger = get_logger(__name__)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    logger.info(f"Saved {len(records)} records to {output_path}")

def main() -> int:
    """
    Main entry point for the filtering script.

    Returns:
        0 on success, 1 on failure.
    """
    setup_logging()
    logger = get_logger(__name__)

    try:
        # Ensure output directory exists
        FILTERED_DATA_DIR.mkdir(parents=True, exist_ok=True)

        # Load raw data
        raw_data = load_raw_data(RAW_DATA_FILE)

        # Filter by target categories
        filtered_data = filter_by_categories(raw_data, TARGET_CATEGORIES)

        # Check for zero results
        if len(filtered_data) == 0:
            error_msg = f"ERROR: Filter returned zero records for categories: {TARGET_CATEGORIES}"
            logger.error(error_msg)
            print(error_msg, file=sys.stderr)
            return 1

        # Save filtered data
        save_filtered_data(filtered_data, FILTERED_DATA_FILE)

        logger.info("Filtering completed successfully.")
        return 0

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Value error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())