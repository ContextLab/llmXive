"""
Task T024: Separate low-confidence / failed samples from raw labels.

This script reads `data/processed/raw_labels.csv`, separates rows with label='null'
into `data/processed/null_samples.csv`, and writes valid rows to `data/processed/labels.csv`.
It also creates an empty `data/processed/excluded_samples.log` if no samples are excluded.
"""
import os
import sys
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
RAW_LABELS_PATH = PROJECT_ROOT / "data" / "processed" / "raw_labels.csv"
NULL_SAMPLES_PATH = PROJECT_ROOT / "data" / "processed" / "null_samples.csv"
FINAL_LABELS_PATH = PROJECT_ROOT / "data" / "processed" / "labels.csv"
EXCLUDED_LOG_PATH = PROJECT_ROOT / "data" / "processed" / "excluded_samples.log"

def load_raw_labels() -> List[Dict[str, Any]]:
    """
    Load the raw labels CSV file.

    Returns:
        List of dictionaries representing each row in the CSV.

    Raises:
        FileNotFoundError: If the raw_labels.csv file does not exist.
        ValueError: If the required columns are missing.
    """
    if not RAW_LABELS_PATH.exists():
        raise FileNotFoundError(f"Raw labels file not found: {RAW_LABELS_PATH}")

    rows = []
    with open(RAW_LABELS_PATH, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        required_columns = {'clip_id', 'label', 'confidence_score', 'reason'}
        if not required_columns.issubset(set(reader.fieldnames or [])):
            raise ValueError(
                f"Missing required columns in {RAW_LABELS_PATH}. "
                f"Expected: {required_columns}, Found: {reader.fieldnames}"
            )
        for row in reader:
            rows.append(row)
    
    logger.info(f"Loaded {len(rows)} rows from {RAW_LABELS_PATH}")
    return rows

def process_labels_and_exclusions(
    raw_rows: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Separate raw rows into valid labels and null samples.

    Args:
        raw_rows: List of dictionaries from the raw labels CSV.

    Returns:
        Tuple of (valid_labels, null_samples).
    """
    valid_labels = []
    null_samples = []

    for row in raw_rows:
        label = row.get('label', '').strip().lower()
        if label == 'null':
            # Ensure we have the specific columns for null_samples
            null_entry = {
                'clip_id': row.get('clip_id', ''),
                'reason': row.get('reason', ''),
                'confidence_score': row.get('confidence_score', '')
            }
            null_samples.append(null_entry)
        else:
            # Keep all columns for valid labels
            valid_labels.append(row)

    logger.info(f"Separated into {len(valid_labels)} valid labels and {len(null_samples)} null samples")
    return valid_labels, null_samples

def save_null_labels(null_samples: List[Dict[str, Any]]) -> None:
    """
    Save null samples to null_samples.csv.

    Args:
        null_samples: List of dictionaries to save.
    """
    if not null_samples:
        logger.warning("No null samples to save.")
        # Create empty file if no samples
        with open(NULL_SAMPLES_PATH, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['clip_id', 'reason', 'confidence_score'])
            writer.writeheader()
        return

    with open(NULL_SAMPLES_PATH, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['clip_id', 'reason', 'confidence_score'])
        writer.writeheader()
        writer.writerows(null_samples)
    
    logger.info(f"Saved {len(null_samples)} null samples to {NULL_SAMPLES_PATH}")

def save_final_labels(valid_labels: List[Dict[str, Any]]) -> None:
    """
    Save valid labels to labels.csv.

    Args:
        valid_labels: List of dictionaries to save.
    """
    if not valid_labels:
        logger.warning("No valid labels to save.")
        # Create empty file if no samples
        with open(FINAL_LABELS_PATH, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['clip_id', 'label', 'confidence_score', 'reason'])
            writer.writeheader()
        return

    # Determine fieldnames from the first row
    fieldnames = list(valid_labels[0].keys())

    with open(FINAL_LABELS_PATH, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(valid_labels)
    
    logger.info(f"Saved {len(valid_labels)} valid labels to {FINAL_LABELS_PATH}")

def save_excluded_log(null_samples: List[Dict[str, Any]]) -> None:
    """
    Create or update the excluded_samples.log file.
    If no samples are excluded, the file is created empty.

    Args:
        null_samples: List of excluded samples.
    """
    with open(EXCLUDED_LOG_PATH, 'w', encoding='utf-8') as f:
        if not null_samples:
            # Create empty file
            f.write("")
        else:
            for sample in null_samples:
                f.write(f"{sample['clip_id']}|{sample['reason']}|{sample['confidence_score']}\n")
    
    logger.info(f"Created excluded log at {EXCLUDED_LOG_PATH} with {len(null_samples)} entries")

def main() -> None:
    """Main entry point for the script."""
    logger.info("Starting T024: Separate low-confidence / failed samples")
    
    try:
        # 1. Load raw labels
        raw_rows = load_raw_labels()
        
        # 2. Process and separate
        valid_labels, null_samples = process_labels_and_exclusions(raw_rows)
        
        # 3. Save artifacts
        save_null_labels(null_samples)
        save_final_labels(valid_labels)
        save_excluded_log(null_samples)
        
        logger.info("T024 completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Invalid data format: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error during T024 execution: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
