"""
Validation module for fingerprint datasets.

This module verifies that the generated crystal dataset meets quality standards:
1. No null values in key columns (SMILES, Space Group, Lattice parameters).
2. Fingerprint bit counts are of a fixed, high-dimensional magnitude (e.g., 2048 bits).

It outputs a JSON validation report to data/validation/fingerprint_check.json.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

# Import project configuration and logging
from config import get_path_data, get_path_processed_data, get_path_validation, ensure_directory
from logging_config import get_logger, log_event
from exceptions import ValidationError

# Constants for validation thresholds
EXPECTED_FINGERPRINT_DIM = 2048
MIN_ACCEPTABLE_DIM = 1024  # Allow some tolerance if implementation varies slightly, but usually exact
KEY_COLUMNS = ['smiles', 'space_group', 'lattice_a', 'lattice_b', 'lattice_c', 'alpha', 'beta', 'gamma']
FINGERPRINT_COLUMN = 'fingerprint'

logger = get_logger(__name__)


def validate_dataset(dataset_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Validates the crystal dataset CSV for nulls and fingerprint dimensions.

    Args:
        dataset_path: Path to the crystal_dataset.csv. If None, uses the default processed path.

    Returns:
        A dictionary containing validation status, error messages, and statistics.
    """
    if dataset_path is None:
        dataset_path = get_path_processed_data("crystal_dataset.csv")

    result = {
        "status": "unknown",
        "path": str(dataset_path),
        "total_rows": 0,
        "null_counts": {},
        "fingerprint_stats": {},
        "errors": [],
        "warnings": []
    }

    logger.info(f"Starting validation for dataset: {dataset_path}")

    if not dataset_path.exists():
        msg = f"Dataset file not found: {dataset_path}"
        logger.error(msg)
        result["status"] = "failed"
        result["errors"].append(msg)
        return result

    try:
        # Load the dataset
        df = pd.read_csv(dataset_path)
        result["total_rows"] = len(df)
        logger.info(f"Loaded dataset with {len(df)} rows.")

        if len(df) == 0:
            msg = "Dataset is empty."
            logger.error(msg)
            result["status"] = "failed"
            result["errors"].append(msg)
            return result

        # 1. Check for nulls in key columns
        null_report = {}
        has_nulls = False
        for col in KEY_COLUMNS:
            if col in df.columns:
                count = df[col].isnull().sum()
                null_report[col] = int(count)
                if count > 0:
                    has_nulls = True
                    msg = f"Column '{col}' has {count} null values."
                    logger.warning(msg)
                    result["warnings"].append(msg)
            else:
                msg = f"Required column '{col}' is missing from the dataset."
                logger.error(msg)
                result["errors"].append(msg)
                has_nulls = True

        result["null_counts"] = null_report

        if has_nulls:
            # Check if critical columns (SMILES, Space Group) have nulls
            critical_nulls = null_report.get('smiles', 0) + null_report.get('space_group', 0)
            if critical_nulls > 0:
                result["status"] = "failed"
                result["errors"].append("Critical columns (SMILES, Space Group) contain null values.")
                return result

        # 2. Check Fingerprint Dimensions
        fp_stats = {}
        if FINGERPRINT_COLUMN not in df.columns:
            msg = f"Required column '{FINGERPRINT_COLUMN}' is missing."
            logger.error(msg)
            result["errors"].append(msg)
            result["status"] = "failed"
            return result

        # Parse the fingerprint column. It is likely stored as a string representation of a list or array.
        # We need to determine the bit length.
        sample_lengths = []
        invalid_rows = 0

        # Take a sample to avoid parsing every single row if the dataset is massive,
        # but ensure we check enough to be confident.
        sample_size = min(1000, len(df))
        sample_df = df.head(sample_size)

        for idx, row in sample_df.iterrows():
            fp_val = row[FINGERPRINT_COLUMN]
            try:
                # Handle different string representations: "[1, 0, ...]" or "1,0,..." or actual list
                if isinstance(fp_val, list):
                    length = len(fp_val)
                elif isinstance(fp_val, str):
                    # Clean and parse
                    clean_str = fp_val.strip().strip('[]')
                    if not clean_str:
                        length = 0
                    else:
                        # Try to split by comma
                        parts = clean_str.split(',')
                        length = len(parts)
                else:
                    length = 0 # Unknown type

                if length > 0:
                    sample_lengths.append(length)
                else:
                    invalid_rows += 1
            except Exception as e:
                logger.warning(f"Error parsing fingerprint at row {idx}: {e}")
                invalid_rows += 1

        if invalid_rows > 0:
            msg = f"Found {invalid_rows} rows with invalid fingerprint format in the sample."
            result["warnings"].append(msg)

        if sample_lengths:
            unique_lengths = set(sample_lengths)
            fp_stats["unique_lengths"] = list(unique_lengths)
            fp_stats["min_length"] = int(min(sample_lengths))
            fp_stats["max_length"] = int(max(sample_lengths))
            fp_stats["mean_length"] = float(np.mean(sample_lengths))
            fp_stats["std_length"] = float(np.std(sample_lengths))

            # Check if the dimension matches expectations
            # We expect a single fixed dimension across all rows
            if len(unique_lengths) == 1:
                actual_dim = sample_lengths[0]
                if actual_dim >= MIN_ACCEPTABLE_DIM:
                    fp_stats["dimension_check"] = "PASS"
                    logger.info(f"Fingerprint dimension check PASSED: {actual_dim} bits.")
                else:
                    fp_stats["dimension_check"] = "FAIL"
                    msg = f"Fingerprint dimension {actual_dim} is below minimum threshold {MIN_ACCEPTABLE_DIM}."
                    result["errors"].append(msg)
                    logger.error(msg)
            else:
                fp_stats["dimension_check"] = "FAIL"
                msg = f"Fingerprints have inconsistent lengths: {unique_lengths}."
                result["errors"].append(msg)
                logger.error(msg)
        else:
            fp_stats["dimension_check"] = "FAIL"
            msg = "Could not determine fingerprint dimensions (all samples invalid)."
            result["errors"].append(msg)

        result["fingerprint_stats"] = fp_stats

        # Final Status Determination
        if result["errors"]:
            result["status"] = "failed"
        else:
            # If we have warnings but no errors, it's a pass with warnings
            result["status"] = "passed"
            if result["warnings"]:
                result["status"] = "passed_with_warnings"

        logger.info(f"Validation completed with status: {result['status']}")

    except Exception as e:
        msg = f"Unexpected error during validation: {str(e)}"
        logger.exception(msg)
        result["status"] = "failed"
        result["errors"].append(msg)
        raise ValidationError(msg) from e

    return result


def main():
    """
    Main entry point to run the validation and save the report.
    """
    # Ensure output directory exists
    output_dir = get_path_validation()
    ensure_directory(output_dir)
    output_path = output_dir / "fingerprint_check.json"

    logger.info(f"Running fingerprint validation. Output will be saved to: {output_path}")

    try:
        validation_result = validate_dataset()

        # Save the result to JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(validation_result, f, indent=2)

        logger.info(f"Validation report saved to {output_path}")

        # Exit with appropriate code
        if validation_result["status"] == "failed":
            logger.error("Validation FAILED. See report for details.")
            sys.exit(1)
        elif validation_result["status"] == "passed_with_warnings":
            logger.warning("Validation PASSED with warnings.")
            sys.exit(0)
        else:
            logger.info("Validation PASSED.")
            sys.exit(0)

    except Exception as e:
        logger.exception(f"Fatal error in main: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()