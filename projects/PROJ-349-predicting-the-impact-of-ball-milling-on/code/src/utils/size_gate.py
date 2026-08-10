"""
Size Gate and Flagged Entry Processor.

This module handles the processing of flagged PSD entries (from T014b)
by attempting OCR extraction (if enabled) and updating the merged dataset.
It also enforces dataset size constraints.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from src.utils.logger import get_module_logger
from src.ingest.ocr_fallback import extract_psd_from_image
from src.config.settings import load_config

# Initialize logger
logger = get_module_logger(__name__)


def read_row_count(row_count_path: Path) -> int:
    """
    Read the row count from a JSON file.

    Args:
        row_count_path: Path to the row_count.json file.

    Returns:
        The number of rows as an integer.

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file content is invalid JSON.
        KeyError: If the 'count' key is missing.
    """
    with open(row_count_path, 'r') as f:
        data = json.load(f)
    return data['count']


def load_flagged_entries(flagged_path: Path) -> List[Dict[str, Any]]:
    """
    Load flagged entries from the JSON file produced by T014b.

    Args:
        flagged_path: Path to data/flagged_psd.json.

    Returns:
        List of flagged entry dictionaries.
    """
    if not flagged_path.exists():
        logger.warning(f"Flagged entries file not found: {flagged_path}. Returning empty list.")
        return []

    try:
        with open(flagged_path, 'r') as f:
            entries = json.load(f)
        logger.info(f"Loaded {len(entries)} flagged entries from {flagged_path}")
        return entries
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse flagged entries JSON: {e}")
        return []


def trigger_ocr_fallback(
    flagged_entries: List[Dict[str, Any]],
    config: Dict[str, Any],
    merged_df: Optional[Any] = None
) -> Optional[Any]:
    """
    Process flagged entries by attempting OCR extraction if enabled.

    This function iterates through flagged entries. If `ocr_enabled` is True in config,
    it calls `extract_psd_from_image` for each entry. If extraction succeeds,
    the extracted PSD values (d10, d50, d90) are returned in a list.
    If extraction fails or OCR is disabled, the entry is skipped/logged.

    Args:
        flagged_entries: List of flagged entry dictionaries.
        config: Configuration dictionary (loaded from config.yaml).
        merged_df: The merged dataframe (optional, for potential in-place update logic if extended).

    Returns:
        A list of successfully extracted PSD records, or None if no extractions occurred.
    """
    ocr_enabled = config.get('ocr', {}).get('enabled', False)
    if not ocr_enabled:
        logger.info("OCR fallback is disabled in config. Skipping extraction for flagged entries.")
        return None

    extracted_records = []
    for entry in flagged_entries:
        entry_id = entry.get('experiment_id', 'unknown')
        image_path_str = entry.get('image_path') # Assuming image_path is stored or derivable

        if not image_path_str:
            logger.warning(f"Entry {entry_id} missing image_path. Skipping.")
            continue

        image_path = Path(image_path_str)
        if not image_path.exists():
            logger.warning(f"Image file not found for entry {entry_id}: {image_path}. Skipping.")
            continue

        try:
            logger.info(f"Attempting OCR extraction for flagged entry: {entry_id}")
            result = extract_psd_from_image(
                image_path=str(image_path),
                flagged_entry_id=entry_id,
                config=config
            )
            if result:
                # Merge original metadata with extracted data
                result['experiment_id'] = entry_id
                result['source'] = entry.get('source', 'OCR_Fallback')
                extracted_records.append(result)
                logger.info(f"Successfully extracted PSD for entry {entry_id}")
            else:
                logger.warning(f"OCR extraction returned empty result for entry {entry_id}.")
        except Exception as e:
            logger.error(f"OCR extraction failed for entry {entry_id}: {e}", exc_info=True)
            # Continue to next entry, do not halt pipeline

    if extracted_records:
        logger.info(f"Successfully extracted {len(extracted_records)} PSD records from flagged entries.")
        return extracted_records
    else:
        logger.warning("No PSD records were successfully extracted from flagged entries.")
        return None


def check_size_gate(count: int, minimum_viable: int = 150) -> None:
    """
    Check if the dataset size meets the minimum viable threshold.

    Args:
        count: Current number of rows in the dataset.
        minimum_viable: Minimum required rows (default 150).

    Raises:
        SystemExit: If count < minimum_viable.
    """
    if count < minimum_viable:
        error_msg = f"Processed dataset size ({count}) < {minimum_viable} experiments (minimum viable) per spec SC-004."
        logger.critical(error_msg)
        raise SystemExit(1)
    else:
        logger.info(f"Dataset size check passed: {count} >= {minimum_viable}")


def run_size_gate_pipeline(
    row_count_path: Path,
    flagged_path: Path,
    merged_df_path: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """
    Main pipeline entry point for T015c: Process Flagged Entries.

    1. Load config.
    2. Load flagged entries.
    3. Attempt OCR extraction if enabled.
    4. (Optional) Update merged dataframe logic could go here if path provided.
    5. Check size gate if row_count_path provided.

    Args:
        row_count_path: Path to row_count.json for size gate check.
        flagged_path: Path to data/flagged_psd.json.
        merged_df_path: Optional path to merged parquet for in-place update (future ext).

    Returns:
        List of extracted records from flagged entries.
    """
    logger.info("Starting T015c: Process Flagged Entries pipeline.")

    # 1. Load Config
    config = load_config()

    # 2. Load Flagged Entries
    flagged_entries = load_flagged_entries(flagged_path)
    if not flagged_entries:
        logger.info("No flagged entries found. Skipping OCR processing.")
        extracted_records = []
    else:
        # 3. Trigger OCR Fallback
        extracted_records = trigger_ocr_fallback(flagged_entries, config)

    # 4. Size Gate Check (if row count file exists)
    if row_count_path and row_count_path.exists():
        try:
            count = read_row_count(row_count_path)
            check_size_gate(count)
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Could not perform size gate check: {e}")
        except SystemExit:
            # Re-raise SystemExit from check_size_gate
            raise
    else:
        logger.info("Row count file not found. Skipping size gate check.")

    logger.info("T015c pipeline completed.")
    return extracted_records or []

def main():
    """CLI entry point for T015c."""
    import argparse
    parser = argparse.ArgumentParser(description="Process flagged PSD entries (T015c)")
    parser.add_argument('--flagged-path', type=str, default='data/flagged_psd.json',
                        help='Path to flagged entries JSON')
    parser.add_argument('--row-count-path', type=str, default='data/processed/row_count.json',
                        help='Path to row count JSON for size gate')
    args = parser.parse_args()

    run_size_gate_pipeline(
        row_count_path=Path(args.row_count_path),
        flagged_path=Path(args.flagged_path)
    )

if __name__ == "__main__":
    main()
