"""
Data Validity Gate for Molecular Excitation Wavelengths.

This module checks for the presence of the 'lambda_max_exp' column in the
processed dataset and flags datasets that only contain computed values.
This reduces the validity score (SC-001) if experimental data is missing.

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
import yaml

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils import get_logger, setup_logging

# Configuration
INPUT_FILE = project_root / "data" / "raw" / "processed.csv"
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
            "sc001_validity": "FAIL"
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
            "sc001_validity": "FAIL"
        }

    # Check for required column
    required_column = "lambda_max_exp"
    has_column = required_column in df.columns

    missing_cols = []
    if not has_column:
        missing_cols.append(required_column)
        logger.warning(f"Missing required column: {required_column}")

    # Check for any lambda_max columns (to detect computed-only datasets)
    lambda_cols = [col for col in df.columns if "lambda_max" in col.lower()]
    logger.info(f"Found lambda_max related columns: {lambda_cols}")

    # Determine if we have experimental data
    has_experimental = False
    if has_column:
        # Check if the column has non-null values
        non_null_count = df[required_column].notna().sum()
        if non_null_count > 0:
            has_experimental = True
            logger.info(f"Found {non_null_count} experimental values in {required_column}")
        else:
            logger.warning(f"Column {required_column} exists but contains no non-null values")

    # Determine SC-001 validity status
    # SC-001 requires experimental data for validity
    if has_experimental:
        sc001_status = "PASS"
        overall_status = "PASS"
        logger.info("Validation PASSED: Experimental data present")
    else:
        sc001_status = "FAIL"
        overall_status = "FAIL"
        logger.warning("Validation FAILED: No experimental data found (computed-only dataset)")

    # Calculate basic statistics if data exists
    stats = {}
    if has_column and has_experimental:
        stats = {
            "count": int(df[required_column].notna().sum()),
            "mean": float(df[required_column].mean()),
            "std": float(df[required_column].std()),
            "min": float(df[required_column].min()),
            "max": float(df[required_column].max())
        }

    return {
        "status": overall_status,
        "has_experimental_data": has_experimental,
        "missing_columns": missing_cols,
        "sc001_validity": sc001_status,
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
    logger.info("Starting Data Validation Gate")
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

    # Exit with error code if validation failed
    if result['status'] == 'FAIL':
        logger.error("Validation failed. Exiting with error code 1.")
        sys.exit(1)
    else:
        logger.info("Validation completed successfully.")
        sys.exit(0)

if __name__ == "__main__":
    main()
