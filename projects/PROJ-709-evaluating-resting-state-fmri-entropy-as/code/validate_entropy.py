"""
Task T019: Validation of Entropy Features
Ensures no NaN values in the final CSV and verifies biologically plausible ranges.
"""
import os
import sys
import logging
import argparse
import numpy as np
import pandas as pd
from pathlib import Path

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import ATLAS_N, TARGET_LENGTH
from utils import setup_logger

# Configuration for biological plausibility
# Sample Entropy (SampEn) for fMRI time series (N=120, m=2) typically falls in range [0.1, 1.5]
# Values < 0.05 indicate near-perfect predictability (noise/artifact)
# Values > 3.0 indicate extreme randomness (likely artifact or calculation error)
MIN_ENTROPY_THRESHOLD = 0.0
MAX_ENTROPY_THRESHOLD = 3.0
MIN_ROWS = 10  # Expect at least some subjects
MIN_COLS = ATLAS_N + 1  # 200 parcels + 1 subject ID column (or similar)

logger = setup_logger(__name__)

def validate_entropy_csv(
    input_path: str,
    min_entropy: float = MIN_ENTROPY_THRESHOLD,
    max_entropy: float = MAX_ENTROPY_THRESHOLD,
    min_rows: int = MIN_ROWS,
    min_cols: int = MIN_COLS
) -> dict:
    """
    Validates the entropy feature CSV file.

    Checks:
    1. File exists and is readable.
    2. No NaN values in numeric columns.
    3. All entropy values are within [min_entropy, max_entropy].
    4. Shape is reasonable (rows >= min_rows, cols >= min_cols).

    Args:
        input_path: Path to the CSV file.
        min_entropy: Minimum allowed entropy value.
        max_entropy: Maximum allowed entropy value.
        min_rows: Minimum expected number of rows.
        min_cols: Minimum expected number of columns.

    Returns:
        dict: Validation results including status, error messages, and stats.
    """
    results = {
        "status": "passed",
        "errors": [],
        "warnings": [],
        "stats": {}
    }

    path = Path(input_path)
    if not path.exists():
        results["status"] = "failed"
        results["errors"].append(f"File not found: {input_path}")
        return results

    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        results["status"] = "failed"
        results["errors"].append(f"Failed to read CSV: {str(e)}")
        return results

    # Check shape
    n_rows, n_cols = df.shape
    results["stats"]["shape"] = (n_rows, n_cols)

    if n_rows < min_rows:
        results["warnings"].append(f"Low number of rows: {n_rows} < {min_rows}")
    
    if n_cols < min_cols:
        results["warnings"].append(f"Low number of columns: {n_cols} < {min_cols}")

    # Identify numeric columns (excluding ID columns if any)
    # Assuming first column might be ID, rest are entropy values
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if not numeric_cols:
        results["status"] = "failed"
        results["errors"].append("No numeric columns found in CSV")
        return results

    # Check for NaN values
    nan_counts = df[numeric_cols].isna().sum()
    total_nan = nan_counts.sum()

    if total_nan > 0:
        results["status"] = "failed"
        results["errors"].append(f"Found {total_nan} NaN values in numeric columns.")
        for col, count in nan_counts[nan_counts > 0].items():
            results["errors"].append(f"  - Column '{col}': {count} NaNs")
    else:
        results["stats"]["nan_count"] = 0

    # Check value ranges
    all_values = df[numeric_cols].values.flatten()
    min_val = np.min(all_values)
    max_val = np.max(all_values)

    results["stats"]["min_value"] = float(min_val)
    results["stats"]["max_value"] = float(max_val)
    results["stats"]["mean_value"] = float(np.mean(all_values))
    results["stats"]["std_value"] = float(np.std(all_values))

    if min_val < min_entropy:
        results["warnings"].append(f"Minimum value {min_val:.4f} is below threshold {min_entropy}")
    
    if max_val > max_entropy:
        results["status"] = "failed"
        results["errors"].append(f"Maximum value {max_val:.4f} exceeds threshold {max_entropy}")
        results["errors"].append("This indicates potential calculation errors or artifacts.")

    return results

def main():
    parser = argparse.ArgumentParser(description="Validate entropy feature CSV output")
    parser.add_argument(
        "--input", 
        type=str, 
        default="data/processed/subject_entropy_features.csv",
        help="Path to the entropy features CSV"
    )
    args = parser.parse_args()

    logger.info(f"Validating entropy features from: {args.input}")
    
    results = validate_entropy_csv(args.input)
    
    if results["status"] == "passed":
        logger.info("✅ Validation PASSED")
    else:
        logger.error("❌ Validation FAILED")
    
    if results["warnings"]:
        logger.warning("⚠️ Warnings:")
        for w in results["warnings"]:
            logger.warning(f"   {w}")
    
    if results["errors"]:
        logger.error("🚫 Errors:")
        for e in results["errors"]:
            logger.error(f"   {e}")

    logger.info(f"Stats: {results['stats']}")

    # Exit with error code if failed
    if results["status"] != "passed":
        sys.exit(1)

    return results

if __name__ == "__main__":
    main()