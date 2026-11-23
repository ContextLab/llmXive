"""
Verification script for T027: Store Fairness Metrics

Validates that the metrics.csv file exists, has the correct structure,
and contains valid traceability fields as required by FR-004.
"""

import os
import sys
import pandas as pd
from pathlib import Path
import json
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging_utils import log_disclaimer

PROJECT_ROOT = Path(__file__).parent.parent
ANALYSIS_DIR = PROJECT_ROOT / "data" / "analysis"
METRICS_FILE = ANALYSIS_DIR / "metrics.csv"

REQUIRED_COLUMNS = ['model_id', 'dataset_id', 'protected_attribute', 'metric_name', 'metric_value']
VALID_METRIC_NAMES = [
    'demographic_parity_difference',
    'equalized_odds_difference',
    'predictive_parity',
    'calibration_within_groups',
    'disparate_impact_ratio',
    'false_positive_rate_disparity'
]

def validate_metrics_file():
    """Validate the metrics.csv file structure and content."""
    errors = []
    warnings = []

    # Check if file exists
    if not METRICS_FILE.exists():
        errors.append(f"Metrics file not found: {METRICS_FILE}")
        return False, errors, warnings

    # Load file
    try:
        df = pd.read_csv(METRICS_FILE)
    except Exception as e:
        errors.append(f"Failed to load metrics file: {e}")
        return False, errors, warnings

    # Check required columns
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        errors.append(f"Missing required columns: {missing_cols}")
        return False, errors, warnings

    # Check for empty file
    if df.empty:
        warnings.append("Metrics file is empty (no data rows)")
        # This might be acceptable if no models were trained, but we flag it

    # Validate metric names
    if not df.empty:
        invalid_metrics = [m for m in df['metric_name'].unique() if m not in VALID_METRIC_NAMES]
        if invalid_metrics:
            warnings.append(f"Unexpected metric names found: {invalid_metrics}")

    # Validate traceability fields are not empty
    for col in ['model_id', 'dataset_id', 'protected_attribute']:
        if not df.empty:
            empty_count = df[col].isna().sum()
            if empty_count > 0:
                errors.append(f"Column '{col}' has {empty_count} empty values")

    # Validate metric_value is numeric
    if not df.empty:
        numeric_count = pd.to_numeric(df['metric_value'], errors='coerce').notna().sum()
        total_count = len(df)
        if numeric_count < total_count:
            warnings.append(f"Non-numeric values found in 'metric_value' column: {total_count - numeric_count} entries")

    return len(errors) == 0, errors, warnings

def main():
    """Main execution function."""
    print("=== T027 Verification: Metrics Storage ===")
    log_disclaimer("Findings are associational only; no causal claims are made.")

    success, errors, warnings = validate_metrics_file()

    if warnings:
        print("\nWarnings:")
        for w in warnings:
            print(f"  - {w}")

    if errors:
        print("\nErrors:")
        for e in errors:
            print(f"  - {e}")
        print("\nVerification FAILED")
        sys.exit(1)
    else:
        print("\nVerification PASSED")
        if not warnings:
            print("No warnings or errors found.")
        sys.exit(0)

if __name__ == "__main__":
    main()
