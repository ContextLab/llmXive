import os
import sys
import logging
import pandas as pd
from pathlib import Path

from config import PROJECT_ROOT, OUTPUTS_DIR
from utils.logging import setup_logger

# Ensure output directories exist
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

logger = setup_logger("validate_baseline_results")

RESULTS_FILE = OUTPUTS_DIR / "baseline_results.csv"

REQUIRED_COLUMNS = [
    "material_id",
    "true_energy",
    "predicted_energy",
    "error",
    "mae",
    "rmse"
]

def validate_results_file(file_path: Path) -> bool:
    """
    Validates that the baseline_results.csv file:
    1. Exists.
    2. Contains the required columns: material_id, true_energy, predicted_energy, error, mae, rmse.
    3. Contains at least one row, even if error > 0.1 eV/atom.
    
    Returns True if valid, False otherwise.
    """
    if not file_path.exists():
        logger.error(f"Results file not found: {file_path}")
        return False

    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        logger.error(f"Failed to read results file {file_path}: {e}")
        return False

    # Check for required columns
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns in {file_path}: {missing_cols}")
        return False

    # Check for at least one row
    if len(df) == 0:
        logger.error(f"Results file {file_path} is empty. No predictions generated.")
        return False

    # Validate data types (basic check)
    numeric_cols = ["true_energy", "predicted_energy", "error", "mae", "rmse"]
    for col in numeric_cols:
        if not pd.api.types.is_numeric_dtype(df[col]):
            logger.warning(f"Column {col} is not numeric. Attempting conversion.")
            try:
                df[col] = pd.to_numeric(df[col], errors='raise')
            except Exception:
                logger.error(f"Failed to convert column {col} to numeric.")
                return False

    # Log summary
    high_error_count = (df["error"].abs() > 0.1).sum()
    logger.info(f"Validation passed for {file_path}.")
    logger.info(f"Total rows: {len(df)}")
    logger.info(f"Rows with error > 0.1 eV/atom: {high_error_count}")
    
    return True

def main():
    logger.info("Starting validation of baseline_results.csv...")
    is_valid = validate_results_file(RESULTS_FILE)
    
    if is_valid:
        logger.info("Validation SUCCESS: baseline_results.csv contains predictions and metrics.")
        sys.exit(0)
    else:
        logger.error("Validation FAILED: baseline_results.csv is invalid or missing data.")
        sys.exit(1)

if __name__ == "__main__":
    main()
