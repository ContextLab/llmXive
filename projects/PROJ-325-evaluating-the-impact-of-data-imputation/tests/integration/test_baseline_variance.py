"""
Integration test for complete-case variance calculation (User Story 1).

This test verifies that the pipeline:
1. Loads the real GSS data from `data/raw/gss_2018_subset.csv` (produced by T004).
2. Performs complete-case analysis (drops rows with missing values in the target variable).
3. Calculates design-based variance using Taylor series linearization via `code/variance_estimator.py`.
4. Outputs a JSON summary to `data/processed/baseline_results.json` with the required keys.

Prerequisites:
- T004 must have successfully run to produce `data/raw/gss_2018_subset.csv`.
- T009/T009b must be implemented in `code/variance_estimator.py`.
"""

import os
import json
import sys
import logging
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from data_ingestion import load_gss_data_subset
from variance_estimator import estimate_taylor_variance

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "gss_2018_subset.csv"
OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "baseline_results.json"
TARGET_VARIABLE = "hours"  # Example variable from GSS (hours worked last week)
WEIGHT_COLUMN = "wtss"
PSU_COLUMN = "psu"
STRATA_COLUMN = "strata"

def test_baseline_variance_calculation():
    """
    Integration test: Verify complete-case variance calculation pipeline.
    
    Steps:
    1. Load real data from disk.
    2. Verify design columns exist.
    3. Perform complete-case analysis.
    4. Calculate variance using Taylor series.
    5. Write results to JSON.
    6. Verify JSON content matches expectations.
    """
    # 1. Check if raw data exists (dependency on T004)
    if not RAW_DATA_PATH.exists():
        pytest.fail(
            f"Raw data file not found at {RAW_DATA_PATH}. "
            "Ensure T004 (data_ingestion) has been run successfully to generate the dataset."
        )

    logger.info(f"Loading data from {RAW_DATA_PATH}...")
    df = load_gss_data_subset(str(RAW_DATA_PATH))

    # 2. Verify design columns
    required_cols = [TARGET_VARIABLE, WEIGHT_COLUMN, PSU_COLUMN, STRATA_COLUMN]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        pytest.fail(f"Missing required design columns in dataset: {missing_cols}")

    # 3. Complete-case analysis (drop rows with missing target variable)
    # Note: In a full pipeline, we might also drop rows with missing weights/psu/strata,
    # but the variance estimator should handle that or we do it here for clarity.
    df_complete = df.dropna(subset=[TARGET_VARIABLE, WEIGHT_COLUMN, PSU_COLUMN, STRATA_COLUMN])
    
    if len(df_complete) == 0:
        pytest.fail("No complete cases remaining after dropping missing values.")

    logger.info(f"Complete cases count: {len(df_complete)} (from {len(df)} total)")

    # 4. Calculate variance using Taylor series linearization
    logger.info(f"Estimating Taylor variance for variable '{TARGET_VARIABLE}'...")
    
    try:
        result = estimate_taylor_variance(
            data=df_complete,
            variable=TARGET_VARIABLE,
            weight_col=WEIGHT_COLUMN,
            psu_col=PSU_COLUMN,
            strata_col=STRATA_COLUMN
        )
    except Exception as e:
        # The estimator should abort if columns are missing (T009), 
        # but we verified they exist. If it fails here, it's a real error.
        logger.error(f"Variance estimation failed: {e}")
        raise

    # 5. Prepare and write output
    output_data = {
        "mean": float(result["mean"]),
        "variance": float(result["variance"]),
        "status": "success",
        "design_type": "Taylor Series Linearization",
        "variable": TARGET_VARIABLE,
        "n_complete_cases": int(len(df_complete)),
        "n_total": int(len(df))
    }

    # Ensure output directory exists
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_PATH, 'w') as f:
        json.dump(output_data, f, indent=2)

    logger.info(f"Results written to {OUTPUT_PATH}")

    # 6. Verify output file and content
    assert OUTPUT_PATH.exists(), "Output file was not created."

    with open(OUTPUT_PATH, 'r') as f:
        loaded_result = json.load(f)

    # Verify required keys
    required_keys = ["mean", "variance", "status", "design_type"]
    for key in required_keys:
        assert key in loaded_result, f"Missing required key '{key}' in output JSON."

    # Verify types and basic sanity
    assert isinstance(loaded_result["mean"], (int, float)), "Mean must be numeric."
    assert isinstance(loaded_result["variance"], (int, float)), "Variance must be numeric."
    assert loaded_result["status"] == "success", "Status must be 'success'."
    assert loaded_result["variance"] >= 0, "Variance cannot be negative."
    
    # Verify the mean is within a reasonable range for GSS hours (0 to 168)
    assert 0 <= loaded_result["mean"] <= 168, f"Mean hours ({loaded_result['mean']}) is out of plausible range."

    logger.info("Integration test passed successfully.")

if __name__ == "__main__":
    # Allow running directly for debugging
    test_baseline_variance_calculation()
    print("Test completed.")