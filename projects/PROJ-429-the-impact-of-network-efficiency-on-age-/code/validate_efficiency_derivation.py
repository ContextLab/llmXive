"""
T016: Validate Derivation of Network Efficiency Metrics.

This script verifies that `data/results/network_metrics.csv` was generated
using the correct formulas:
  Global_Efficiency = 1.0 / Characteristic_Path_Length
  Local_Efficiency = 1.0 / Local_Path_Length (or equivalent reciprocal logic)

It reads the CSV, computes the expected values from the path length columns,
compares them to the reported efficiency columns, and writes a verification
report to `data/results/efficiency_check.json`.

Tolerance: max_deviation must be < 1e-6.
"""
import os
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
METRICS_CSV = PROJECT_ROOT / "data" / "results" / "network_metrics.csv"
OUTPUT_JSON = PROJECT_ROOT / "data" / "results" / "efficiency_check.json"

# Column names expected in the CSV based on metrics.py implementation
# Assuming standard graph metrics output
COL_GLOBAL_EFF = 'global_efficiency'
COL_LOCAL_EFF = 'local_efficiency'
COL_PATH_LEN = 'characteristic_path_length'
COL_LOCAL_PATH_LEN = 'local_path_length'  # Often derived similarly or explicitly stored

def validate_efficiency_formulas():
    """
    Validates the reciprocal relationship between efficiency and path length.
    Returns a dict with verification status and max deviation.
    """
    if not METRICS_CSV.exists():
        raise FileNotFoundError(
            f"Required file not found: {METRICS_CSV}. "
            "Ensure T008_run has been executed successfully."
        )

    logger.info(f"Loading metrics from {METRICS_CSV}")
    df = pd.read_csv(METRICS_CSV)

    # Check for required columns
    required_cols = [COL_GLOBAL_EFF, COL_PATH_LEN]
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Missing required columns in {METRICS_CSV}: {missing_cols}. "
            "The metrics generation script (T008) may have used different column names."
        )

    # Handle Local Efficiency if column exists, otherwise skip or assume N/A
    has_local = COL_LOCAL_EFF in df.columns and COL_LOCAL_PATH_LEN in df.columns

    deviations_global = []
    deviations_local = []
    valid_rows = 0

    for idx, row in df.iterrows():
        # Skip rows with NaN values in critical columns
        if pd.isna(row[COL_PATH_LEN]) or pd.isna(row[COL_GLOBAL_EFF]):
            continue

        # Avoid division by zero
        if row[COL_PATH_LEN] == 0:
            logger.warning(f"Row {idx}: Path length is 0, skipping global efficiency check.")
            continue

        # Check Global Efficiency: E_global = 1 / L
        expected_global = 1.0 / row[COL_PATH_LEN]
        actual_global = row[COL_GLOBAL_EFF]
        
        # Calculate absolute deviation
        # Use relative error if values are very small, but task asks for deviation < 1e-6
        # Absolute difference is safer for the < 1e-6 constraint on typical float values
        dev_global = abs(expected_global - actual_global)
        deviations_global.append(dev_global)
        valid_rows += 1

        if has_local:
            if pd.isna(row[COL_LOCAL_PATH_LEN]) or row[COL_LOCAL_PATH_LEN] == 0:
                continue
            expected_local = 1.0 / row[COL_LOCAL_PATH_LEN]
            actual_local = row[COL_LOCAL_EFF]
            dev_local = abs(expected_local - actual_local)
            deviations_local.append(dev_local)

    if valid_rows == 0:
        logger.warning("No valid rows found to validate. Marking as failed.")
        return {
            "formula_verified": False,
            "max_deviation": float('inf'),
            "reason": "No valid data rows found."
        }

    max_dev_global = max(deviations_global) if deviations_global else 0.0
    max_dev_local = max(deviations_local) if has_local and deviations_local else 0.0
    
    overall_max_dev = max(max_dev_global, max_dev_local)
    is_verified = overall_max_dev < 1e-6

    logger.info(f"Validated {valid_rows} rows.")
    logger.info(f"Max deviation (Global): {max_dev_global:.2e}")
    if has_local:
        logger.info(f"Max deviation (Local): {max_dev_local:.2e}")
    logger.info(f"Overall Max Deviation: {overall_max_dev:.2e}")
    logger.info(f"Verification Status: {'PASSED' if is_verified else 'FAILED'} (Tolerance: 1e-6)")

    return {
        "formula_verified": is_verified,
        "max_deviation": float(overall_max_dev)
    }

def main():
    try:
        result = validate_efficiency_formulas()
        
        # Ensure output directory exists
        OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
        
        # Write result
        with open(OUTPUT_JSON, 'w') as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"Verification report written to {OUTPUT_JSON}")
        
        if not result["formula_verified"]:
            logger.error("Formula verification FAILED. Check max_deviation.")
            # Do not exit with error code to allow the pipeline to continue if desired, 
            # but the report clearly states failure.
            # However, strict validation might require exit 1. 
            # Given T016 is a validation task, we report the failure.
        
    except Exception as e:
        logger.error(f"Validation failed with exception: {e}")
        # Write a failure report if possible, or let the exception propagate
        OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_JSON, 'w') as f:
            json.dump({
                "formula_verified": False,
                "max_deviation": float('inf'),
                "error": str(e)
            }, f, indent=2)
        raise

if __name__ == "__main__":
    main()
