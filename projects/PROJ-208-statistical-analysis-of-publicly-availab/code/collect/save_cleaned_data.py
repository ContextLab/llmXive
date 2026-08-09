"""
Save cleaned dataset to CSV with checksum and validate completeness.

This script loads preprocessed issues from the Parquet file, saves them to CSV,
calculates a checksum for reproducibility, and validates that the dataset meets
the ≥95% completeness threshold for required columns.
"""

import json
import hashlib
import logging
import sys
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config import get_config, get_path
from utils.validators import validate_dataset_schema, ValidationError


def load_preprocessed_issues(input_path: Path) -> List[Dict[str, Any]]:
    """Load preprocessed issues from Parquet file."""
    try:
        import pandas as pd
        df = pd.read_parquet(input_path)
        logging.info(f"Loaded {len(df)} issues from {input_path}")
        return df.to_dict('records')
    except Exception as e:
        logging.error(f"Failed to load preprocessed issues: {e}")
        raise


def calculate_checksum(data: List[Dict[str, Any]], algorithm: str = 'sha256') -> str:
    """Calculate checksum of the dataset for reproducibility verification."""
    # Convert to JSON string for consistent hashing
    json_str = json.dumps(data, sort_keys=True, separators=(',', ':'))
    return hashlib.new(algorithm, json_str.encode('utf-8')).hexdigest()


def validate_completeness(
    data: List[Dict[str, Any]],
    required_columns: List[str],
    threshold: float = 0.95
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate that required columns are populated for at least threshold percentage of rows.

    Args:
        data: List of issue dictionaries
        required_columns: List of column names to check
        threshold: Minimum completeness ratio (default 0.95)

    Returns:
        Tuple of (passed, details) where details contains per-column completeness
    """
    if not data:
        logging.error("No data to validate")
        return False, {"error": "Empty dataset"}

    total_rows = len(data)
    completeness = {}
    failed_columns = []

    for col in required_columns:
        populated_count = sum(1 for row in data if row.get(col) is not None and row.get(col) != '')
        completeness_ratio = populated_count / total_rows
        completeness[col] = {
            "populated_count": populated_count,
            "total_count": total_rows,
            "ratio": completeness_ratio,
            "passed": completeness_ratio >= threshold
        }
        if completeness_ratio < threshold:
            failed_columns.append(col)

    overall_passed = len(failed_columns) == 0
    details = {
        "overall_passed": overall_passed,
        "threshold": threshold,
        "required_columns": required_columns,
        "completeness": completeness,
        "failed_columns": failed_columns
    }

    if overall_passed:
        logging.info(f"Completeness validation PASSED (≥{threshold*100}% for all required columns)")
    else:
        logging.warning(f"Completeness validation FAILED: {failed_columns} below {threshold*100}% threshold")

    return overall_passed, details


def save_metadata(
    output_path: Path,
    checksum: str,
    validation_results: Dict[str, Any],
    row_count: int
) -> None:
    """Save metadata about the saved dataset."""
    metadata = {
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "row_count": row_count,
        "checksum_sha256": checksum,
        "completeness_validation": validation_results
    }

    metadata_path = output_path.parent / f"{output_path.stem}_metadata.json"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    logging.info(f"Saved metadata to {metadata_path}")


def main() -> int:
    """Main entry point for saving cleaned data."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    config = get_config()
    input_path = get_path(config, 'raw_parquet')
    output_path = get_path(config, 'cleaned_csv')

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logging.info(f"Loading preprocessed issues from {input_path}")
    data = load_preprocessed_issues(input_path)

    # Define required columns per SC-001
    required_columns = ['created_at', 'closed_at', 'labels', 'assignee', 'comments_count']
    completeness_threshold = get_threshold(config, 'completeness_threshold', 0.95)

    logging.info(f"Validating completeness (threshold: {completeness_threshold*100}%)")
    passed, validation_details = validate_completeness(data, required_columns, completeness_threshold)

    if not passed:
        logging.error("Completeness validation failed. Dataset does not meet requirements.")
        # Still save the data but mark validation as failed
        # The pipeline should not proceed to analysis if this fails

    # Save to CSV
    logging.info(f"Saving {len(data)} issues to {output_path}")
    if data:
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)

    # Calculate checksum
    checksum = calculate_checksum(data)
    logging.info(f"Dataset checksum (SHA256): {checksum}")

    # Save metadata
    save_metadata(output_path, checksum, validation_details, len(data))

    # Log summary
    logging.info("=" * 60)
    logging.info("CLEANED DATA SAVE SUMMARY")
    logging.info("=" * 60)
    logging.info(f"Input: {input_path}")
    logging.info(f"Output: {output_path}")
    logging.info(f"Rows: {len(data)}")
    logging.info(f"Checksum: {checksum}")
    logging.info(f"Completeness Passed: {validation_details['overall_passed']}")
    if not validation_details['overall_passed']:
        logging.warning(f"Failed columns: {validation_details['failed_columns']}")
    logging.info("=" * 60)

    # Return non-zero exit code if validation failed
    return 0 if validation_details['overall_passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
