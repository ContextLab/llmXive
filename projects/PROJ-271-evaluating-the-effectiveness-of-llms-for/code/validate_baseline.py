"""
Validation script for User Story 1 (T012).

Validates that `data/static_baseline.csv` contains >= 95% of the sampled
functions with all required columns as per FR-001 and SC-005.

Required columns:
- code
- loc
- cyclomatic_complexity
- static_smell_labels

Threshold: >= 95% of rows must be complete.
"""
import os
import sys
import logging
import pandas as pd
from pathlib import Path

# Add project root to path for imports if running as script
# Assuming this file is in code/, we need to import config from the same level
# The execution environment should handle path setup, but we add a safety check.
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.config import get_data_path, setup_logging

# Configure logging
logger = setup_logging("validation")

REQUIRED_COLUMNS = ["code", "loc", "cyclomatic_complexity", "static_smell_labels"]
VALIDATION_THRESHOLD = 0.95
EXPECTED_SAMPLE_SIZE = 800  # Defined in T007

def validate_baseline():
    """
    Validates the static baseline CSV file.
    
    Returns:
        bool: True if validation passes, False otherwise.
    """
    data_path = get_data_path()
    baseline_file = data_path / "static_baseline.csv"
    
    if not baseline_file.exists():
        logger.error(f"Baseline file not found: {baseline_file}")
        logger.error("Run data_pipeline.py first to generate the baseline.")
        return False
    
    try:
        df = pd.read_csv(baseline_file)
    except Exception as e:
        logger.error(f"Failed to read baseline CSV: {e}")
        return False
    
    total_rows = len(df)
    logger.info(f"Loaded {total_rows} rows from {baseline_file}")
    
    if total_rows == 0:
        logger.error("Baseline file is empty.")
        return False
    
    # Check for required columns
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        logger.error(f"Available columns: {list(df.columns)}")
        return False
    
    logger.info("All required columns present.")
    
    # Check for completeness (non-null values in required columns)
    # We treat empty strings or NaN as invalid for 'code' and 'labels'
    # For numeric metrics, we check for NaN
    completeness_mask = df[REQUIRED_COLUMNS].notna().all(axis=1)
    
    # Additional check: 'code' and 'static_smell_labels' should not be empty strings
    if 'code' in df.columns:
        completeness_mask &= (df['code'].str.strip() != "")
    if 'static_smell_labels' in df.columns:
        completeness_mask &= (df['static_smell_labels'].str.strip() != "")
    
    valid_rows = completeness_mask.sum()
    completeness_ratio = valid_rows / total_rows if total_rows > 0 else 0.0
    
    logger.info(f"Valid rows: {valid_rows} / {total_rows} ({completeness_ratio:.2%})")
    logger.info(f"Expected sample size: ~{EXPECTED_SAMPLE_SIZE}")
    
    # Check against threshold
    if completeness_ratio < VALIDATION_THRESHOLD:
        logger.error(
            f"Validation FAILED: Completeness ratio {completeness_ratio:.2%} "
            f"is below required threshold {VALIDATION_THRESHOLD:.2%}."
        )
        return False
    
    # Check if we have a reasonable number of rows (close to expected 800)
    # Allowing some tolerance for filtering errors in T010
    if valid_rows < EXPECTED_SAMPLE_SIZE * 0.90:
        logger.warning(
            f"Row count ({valid_rows}) is significantly lower than expected "
            f"({EXPECTED_SAMPLE_SIZE}). Some data loss may have occurred."
        )
    
    logger.info("Validation PASSED: Baseline meets quality requirements.")
    return True

def main():
    """Entry point for the validation script."""
    success = validate_baseline()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()