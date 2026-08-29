"""
Data Validity Gate for Molecular Excitation Wavelengths.

This module checks for the presence of the 'lambda_max_exp' column in the
processed dataset. If only computed values exist (no experimental data),
it explicitly logs the limitation and reframes SC-001 to "prediction of
computed values" without silently reducing validity.

Usage:
    python code/validate_data.py
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils import get_logger, setup_logging

# Configuration
# T008 outputs to data/processed/cleaned.csv
INPUT_FILE = project_root / "data" / "processed" / "cleaned.csv"
OUTPUT_FILE = project_root / "data" / "processed" / "validation_report.json"
LOG_FILE = project_root / "data" / "logs" / "validate_data.log"

# Ensure log directory exists
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

def validate_data(input_path: Path) -> Dict[str, Any]:
    """
    Validate the input dataset for experimental lambda_max values.

    Args:
        input_path: Path to the input CSV file.

    Returns:
        Dictionary containing validation results and status.
    """
    logger = get_logger("validate_data")
    logger.info(f"Starting validation for {input_path}")

    if not input_path.exists():
        error_msg = f"Input file not found: {input_path}"
        logger.error(error_msg)
        return {
            "status": "FAIL",
            "error": error_msg,
            "has_experimental_data": False,
            "missing_columns": ["lambda_max_exp"],
            "sc001_validity": "FAIL",
            "sc001_reframed": False,
            "limitation_log": "Input file missing."
        }

    try:
        # Load data with chunking for memory efficiency if needed
        # Using chunksize=100000 to handle large files within 7GB RAM
        chunks = []
        for chunk in pd.read_csv(input_path, chunksize=100000):
            chunks.append(chunk)

        df = pd.concat(chunks, ignore_index=True)
        logger.info(f"Loaded {len(df)} rows")

    except Exception as e:
        error_msg = f"Failed to load CSV: {str(e)}"
        logger.error(error_msg)
        return {
            "status": "FAIL",
            "error": error_msg,
            "has_experimental_data": False,
            "missing_columns": ["lambda_max_exp"],
            "sc001_validity": "FAIL",
            "sc001_reframed": False,
            "limitation_log": error_msg
        }

    # Check for required column
    required_column = "lambda_max_exp"
    has_column = required_column in df.columns

    missing_cols = []
    if not has_column:
        missing_cols.append(required_column)
        logger.warning(f"Missing required column: {required_column}")
        # If the column is missing entirely, we cannot validate experimental data.
        # We must fail loud as per constraints, but also log the specific limitation.
        limitation_msg = (
            f"Column '{required_column}' is missing from dataset. "
            "Cannot validate experimental data. SC-001 validity fails."
        )
        logger.error(limitation_msg)
        return {
            "status": "FAIL",
            "has_experimental_data": False,
            "missing_columns": missing_cols,
            "sc001_validity": "FAIL",
            "sc001_reframed": False,
            "limitation_log": limitation_msg,
            "total_rows": len(df),
            "input_file": str(input_path)
        }

    # Check for any lambda_max columns (to detect computed-only datasets)
    lambda_cols = [col for col in df.columns if "lambda_max" in col.lower()]
    logger.info(f"Found lambda_max related columns: {lambda_cols}")

    # Determine if we have experimental data
    # We check if the column has non-null values.
    # If the column exists but is all NaN, it implies computed-only or missing data.
    non_null_count = df[required_column].notna().sum()
    has_experimental = non_null_count > 0

    if has_experimental:
        logger.info(f"Found {non_null_count} experimental values in {required_column}")
        sc001_status = "PASS"
        overall_status = "PASS"
        sc001_reframed = False
        limitation_log = "Experimental data present."
    else:
        # The column exists but contains no non-null values.
        # This indicates a computed-only dataset or a data ingestion failure.
        # Per task T009: "If only computed values exist, reframe SC-001... and log the limitation explicitly"
        logger.warning(f"Column {required_column} exists but contains no non-null values (Computed-only dataset detected).")
        
        sc001_status = "FAIL" # Fails the strict experimental gate
        overall_status = "FAIL"
        sc001_reframed = True
        limitation_log = (
            "Dataset contains only computed values for 'lambda_max_exp' (no experimental data found). "
            "SC-001 validity gate FAILS for experimental prediction. "
            "SC-001 is effectively reframed to 'prediction of computed values' for this run. "
            "Limitation logged explicitly as per T009 requirements."
        )
        logger.warning(limitation_log)

    # Calculate basic statistics if data exists
    stats = {}
    if has_column:
        stats = {
            "count": int(non_null_count),
            "mean": float(df[required_column].mean()) if non_null_count > 0 else None,
            "std": float(df[required_column].std()) if non_null_count > 0 else None,
            "min": float(df[required_column].min()) if non_null_count > 0 else None,
            "max": float(df[required_column].max()) if non_null_count > 0 else None
        }

    return {
        "status": overall_status,
        "has_experimental_data": has_experimental,
        "missing_columns": missing_cols,
        "sc001_validity": sc001_status,
        "sc001_reframed": sc001_reframed,
        "limitation_log": limitation_log,
        "column_stats": stats,
        "total_rows": len(df),
        "input_file": str(input_path),
        "validation_columns_checked": lambda_cols
    }

def main():
    """Main entry point for the validation script."""
    setup_logging(LOG_FILE)
    logger = get_logger("validate_data")

    logger.info("=" * 60)
    logger.info("Starting Data Validity Gate (T009)")
    logger.info("=" * 60)

    # Run validation
    result = validate_data(INPUT_FILE)

    # Ensure output directory exists
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Write results to JSON
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(result, f, indent=2)

    logger.info(f"Validation report written to: {OUTPUT_FILE}")
    logger.info(f"Status: {result['status']}")
    logger.info(f"SC-001 Validity: {result['sc001_validity']}")
    if result.get('sc001_reframed'):
        logger.warning(f"SC-001 Reframed: {result['limitation_log']}")

    # Exit with error code if validation failed
    # This enforces the "fail loud" policy if experimental data is missing
    if result['status'] == 'FAIL':
        logger.error("Validation failed. Exiting with error code 1.")
        sys.exit(1)
    else:
        logger.info("Validation completed successfully.")
        sys.exit(0)

if __name__ == "__main__":
    main()