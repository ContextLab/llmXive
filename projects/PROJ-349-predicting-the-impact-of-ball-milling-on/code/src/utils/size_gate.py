"""
Size Gate Utility for Ball Milling Dataset Pipeline.

This module implements the pre-processing size gate logic:
1. Reads the row count from data/processed/row_count.json.
2. Logs a critical warning if count < 150 (does not halt).
3. If flagged PSD entries exist in data/flagged_psd.json, triggers
   the OCR extraction fallback (T014c) for each entry before returning.
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import the OCR fallback function from the ingest module as per task dependency
# The function signature is expected to be: extract_psd_from_image(image_path, flagged_entry_id) -> dict
from src.ingest.ocr_fallback import extract_psd_from_image
from src.utils.logger import get_module_logger

logger = get_module_logger(__name__)

# Constants for paths (relative to project root)
ROW_COUNT_PATH = Path("data/processed/row_count.json")
FLAGGED_PSD_PATH = Path("data/flagged_psd.json")
MIN_ROWS_WARNING = 150

def read_row_count() -> int:
    """
    Reads the row count from the processed row_count.json file.

    Returns:
        int: The number of rows. Returns 0 if file not found or invalid.

    Raises:
        FileNotFoundError: If the row_count.json file does not exist.
        json.JSONDecodeError: If the file content is not valid JSON.
    """
    if not ROW_COUNT_PATH.exists():
        raise FileNotFoundError(f"Row count file not found: {ROW_COUNT_PATH}")

    with open(ROW_COUNT_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if 'count' not in data:
        raise ValueError(f"Invalid format in {ROW_COUNT_PATH}: missing 'count' key")

    return int(data['count'])

def load_flagged_entries() -> List[Dict[str, Any]]:
    """
    Loads the list of flagged PSD entries from data/flagged_psd.json.

    Returns:
        List[Dict]: A list of flagged entry dictionaries.
        Returns an empty list if the file does not exist or is empty.
    """
    if not FLAGGED_PSD_PATH.exists():
        logger.debug(f"Flagged PSD file not found at {FLAGGED_PSD_PATH}. No OCR trigger needed.")
        return []

    try:
        with open(FLAGGED_PSD_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not isinstance(data, list):
            logger.warning(f"Flagged PSD file {FLAGGED_PSD_PATH} does not contain a list. Ignoring.")
            return []

        return data
    except json.JSONDecodeError as e:
        logger.warning(f"Could not parse flagged PSD file {FLAGGED_PSD_PATH}: {e}")
        return []

def trigger_ocr_fallback(flagged_entries: List[Dict[str, Any]]) -> int:
    """
    Iterates through flagged entries and calls the OCR extraction function.

    This implements the requirement to attempt extraction for flagged entries
    before the pipeline proceeds.

    Args:
        flagged_entries: List of dictionaries containing flagged entry data.
                         Expected keys: 'experiment_id', 'issue_type', 'raw_blob_hash', etc.

    Returns:
        int: The number of entries successfully processed (or attempted).
    """
    if not flagged_entries:
        return 0

    logger.info(f"Starting OCR fallback extraction for {len(flagged_entries)} flagged entries.")
    processed_count = 0

    for entry in flagged_entries:
        entry_id = entry.get('experiment_id', 'unknown_id')
        image_path = entry.get('image_path') # Assuming the image path is stored here or derived

        # If image_path is not directly in the entry, we might need to reconstruct it
        # or the entry might just be a reference. The task says "call extract_psd_from_image".
        # We assume the entry contains necessary metadata or the function handles the lookup.
        # Based on T014c signature: extract_psd_from_image(image_path: str, flagged_entry_id: str)

        if not image_path:
            logger.warning(f"Entry {entry_id} is missing 'image_path'. Skipping OCR attempt.")
            continue

        try:
            logger.debug(f"Attempting OCR extraction for entry {entry_id} from {image_path}")
            # Call the OCR function defined in T014c
            extracted_data = extract_psd_from_image(image_path, entry_id)
            
            # Log success or specific extraction details if needed
            # The task requires the call to happen. We assume the function updates state
            # or returns data to be merged later.
            logger.info(f"OCR extraction completed for entry {entry_id}.")
            processed_count += 1

        except Exception as e:
            # Log the error but continue processing other entries
            logger.error(f"OCR extraction failed for entry {entry_id}: {e}")
            # Do not halt; the task is to attempt extraction.

    logger.info(f"OCR fallback process finished. Processed {processed_count} entries.")
    return processed_count

def check_size_gate() -> bool:
    """
    Main entry point for the pre-processing size gate.

    1. Reads the row count.
    2. Logs a critical warning if < 150 rows.
    3. Triggers OCR fallback if flagged entries exist.

    Returns:
        bool: True if the check passed (or warning issued), False if file not found.
              (Returns True to allow pipeline to continue even on warning, as per spec).
    
    Note: This function does NOT halt the pipeline (no SystemExit).
    """
    logger.info("Executing pre-processing size gate check.")

    try:
        count = read_row_count()
    except FileNotFoundError:
        logger.error("Row count file not found. Cannot perform size gate check.")
        return False
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Error reading row count file: {e}")
        return False

    logger.info(f"Current dataset row count: {count}")

    if count < MIN_ROWS_WARNING:
        logger.warning(
            f"CRITICAL WARNING: Dataset size ({count} rows) is below the target threshold ({MIN_ROWS_WARNING}). "
            "Proceeding with caution as per pre-processing gate policy."
        )
    else:
        logger.info(f"Dataset size ({count} rows) meets the target threshold ({MIN_ROWS_WARNING}).")

    # CRITICAL: Trigger OCR fallback if flagged entries exist
    flagged_entries = load_flagged_entries()
    if flagged_entries:
        logger.info(f"Detected {len(flagged_entries)} flagged PSD entries. Triggering OCR extraction fallback.")
        trigger_ocr_fallback(flagged_entries)
    else:
        logger.debug("No flagged PSD entries found. Skipping OCR fallback.")

    return True

if __name__ == "__main__":
    # Simple CLI for manual testing if needed
    logging.basicConfig(level=logging.INFO)
    success = check_size_gate()
    if success:
        print("Size gate check completed successfully.")
    else:
        print("Size gate check failed (file not found or invalid).")
