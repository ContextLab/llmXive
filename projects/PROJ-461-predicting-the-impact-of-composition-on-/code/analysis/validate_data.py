import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from config import Config, load_config
from utils.logger import get_logger

logger = get_logger(__name__)


def validate_numeric_types(df: pd.DataFrame, columns: List[str]) -> Dict[str, Any]:
    """
    Validate that specified columns contain valid numeric types (int/float).
    Returns a dict with column-wise validity status and error details.
    """
    results = {}
    all_valid = True

    for col in columns:
        if col not in df.columns:
            results[col] = {
                "valid": False,
                "error": f"Column '{col}' not found in DataFrame"
            }
            all_valid = False
            continue

        series = df[col]
        # Check if the dtype is numeric or can be coerced
        try:
            numeric_series = pd.to_numeric(series, errors='raise')
            # Check for any non-finite values (inf, -inf) which are technically numeric but often invalid for ML
            if not np.isfinite(numeric_series).all():
                results[col] = {
                    "valid": False,
                    "error": "Contains non-finite values (inf, -inf)",
                    "dtype": str(series.dtype)
                }
                all_valid = False
            else:
                results[col] = {
                    "valid": True,
                    "dtype": str(numeric_series.dtype)
                }
        except (ValueError, TypeError) as e:
            results[col] = {
                "valid": False,
                "error": str(e),
                "dtype": str(series.dtype)
            }
            all_valid = False

    return {"all_valid": all_valid, "details": results}


def validate_missing_values(df: pd.DataFrame, target_column: str) -> Dict[str, Any]:
    """
    Validate that the target column has zero missing values.
    Returns a dict with missing value stats.
    """
    missing_count = df[target_column].isna().sum()
    total_count = len(df)

    return {
        "target_column": target_column,
        "total_rows": total_count,
        "missing_count": int(missing_count),
        "missing_percentage": float((missing_count / total_count * 100) if total_count > 0 else 0),
        "is_valid": missing_count == 0
    }


def run_validation(
    data_path: Path,
    target_column: str = "density",
    composition_columns: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Run full validation on the dataset.
    - Checks for missing values in the target column.
    - Checks for valid numeric types in specified columns.
    - Generates a summary log.
    """
    config = load_config()
    logger.info(f"Starting validation for data at: {data_path}")

    if not data_path.exists():
        logger.error(f"Data file not found: {data_path}")
        raise FileNotFoundError(f"Data file not found: {data_path}")

    df = pd.read_csv(data_path)
    logger.info(f"Loaded data with {len(df)} rows and {len(df.columns)} columns")

    # Default composition columns if not provided (heuristic based on typical naming)
    if composition_columns is None:
        # Look for columns that might represent elemental fractions (e.g., Fe, Cu, or mass_fraction_*)
        # For this specific task, we assume the CSV has a 'composition' dict or specific element columns.
        # We will validate all numeric columns except the target as potential mass fractions.
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        composition_columns = [c for c in numeric_cols if c != target_column]

    # 1. Validate Missing Values
    missing_stats = validate_missing_values(df, target_column)
    if not missing_stats["is_valid"]:
        logger.warning(f"Target column '{target_column}' has {missing_stats['missing_count']} missing values.")

    # 2. Validate Numeric Types
    type_stats = validate_numeric_types(df, composition_columns)
    if not type_stats["all_valid"]:
        logger.warning("Some composition columns have invalid numeric types.")

    # 3. Compile Validation Log
    validation_log = {
        "source_file": str(data_path),
        "row_count": len(df),
        "column_count": len(df.columns),
        "target_column": target_column,
        "missing_value_stats": missing_stats,
        "numeric_type_validation": type_stats,
        "overall_status": "PASS" if (missing_stats["is_valid"] and type_stats["all_valid"]) else "FAIL",
        "timestamp": pd.Timestamp.now().isoformat()
    }

    logger.info(f"Validation completed. Status: {validation_log['overall_status']}")
    return validation_log


def main():
    """
    Main entry point for data validation.
    Reads data from 'data/clean_data.csv' or 'data/synthetic_data.csv',
    validates it, and writes 'data/validation_log.json'.
    """
    config = load_config()
    data_dir = config.data_dir

    # Determine which file to validate
    clean_path = data_dir / "clean_data.csv"
    synthetic_path = data_dir / "synthetic_data.csv"

    target_file = None
    source_status = "unknown"

    if clean_path.exists():
        target_file = clean_path
        source_status = "clean_data"
    elif synthetic_path.exists():
        target_file = synthetic_path
        source_status = "synthetic_data"
    else:
        logger.error("Neither clean_data.csv nor synthetic_data.csv found.")
        # Create a failure log if no data exists
        failure_log = {
            "source_file": "none",
            "source_status": "none",
            "overall_status": "FAIL",
            "error": "No data file found to validate"
        }
        output_path = data_dir / "validation_log.json"
        with open(output_path, "w") as f:
            json.dump(failure_log, f, indent=2)
        return

    logger.info(f"Validating file: {target_file} (Source: {source_status})")

    try:
        log_data = run_validation(target_file, target_column="density")
        log_data["source_status"] = source_status

        # Save the log
        output_path = data_dir / "validation_log.json"
        with open(output_path, "w") as f:
            json.dump(log_data, f, indent=2)

        logger.info(f"Validation log saved to: {output_path}")

        # Exit with error code if validation failed
        if log_data["overall_status"] == "FAIL":
            logger.error("Validation failed. Check logs for details.")
            import sys
            sys.exit(1)

    except Exception as e:
        logger.error(f"Validation process failed with exception: {e}", exc_info=True)
        import sys
        sys.exit(1)


if __name__ == "__main__":
    main()