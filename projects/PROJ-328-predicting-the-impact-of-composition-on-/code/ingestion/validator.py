"""
T014: Implement validation reporting logic.
Checks for non-null hardness, complete composition, and writes ingestion status.
"""
import os
import sys
import json
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from config import get_data_processed_dir, get_composition_sum_threshold, get_min_n_for_power, get_target_n
from utils.logging_config import get_logger

logger = get_logger(__name__)

PROCESSED_DIR = get_data_processed_dir()
CLEANED_FILE = PROCESSED_DIR / "solder_hardness_cleaned.csv"
FILTERED_FILE = PROCESSED_DIR / "filtered_records.csv"
STATUS_FILE = PROCESSED_DIR / ".ingestion_status.json"

def validate_and_write_status():
    """
    1. Read cleaned data.
    2. Verify composition sums (should all be >= threshold).
    3. Count non-null hardness.
    4. Read filtered records count.
    5. Write .ingestion_status.json.
    """
    if not CLEANED_FILE.exists():
        logger.error(f"Cleaned data file not found: {CLEANED_FILE}")
        sys.exit(1)

    df = pd.read_csv(CLEANED_FILE)
    threshold = get_composition_sum_threshold()
    min_n_power = get_min_n_for_power()
    target_n = get_target_n()

    logger.info(f"Validating {len(df)} records in {CLEANED_FILE}")

    # 1. Calculate composition sums explicitly to confirm validity
    # Identify columns that are likely elemental compositions (numeric, not hardness/ID)
    # Assuming columns like 'Sn', 'Pb', 'Ag', etc. are present.
    # We'll select numeric columns that are not the target or metadata.
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    # Exclude known non-composition numeric columns if any (e.g., 'hardness_hv' is target)
    # We assume the target is 'hardness_hv'
    composition_cols = [c for c in numeric_cols if c != 'hardness_hv' and c != 'measurement_temp_c']
    
    if not composition_cols:
        logger.warning("No composition columns found. Assuming all numeric cols except hardness are composition.")
        composition_cols = [c for c in numeric_cols if c != 'hardness_hv']

    if composition_cols:
        df['composition_sum'] = df[composition_cols].sum(axis=1)
        # Check for any violations
        violations = df[df['composition_sum'] < threshold]
        if not violations.empty:
            logger.warning(f"Found {len(violations)} records with composition sum < {threshold}. "
                           "These should have been filtered in T013.")
            # Log them but do not fail the whole pipeline, as T013 should have handled this.
            # We just record the count of violations for the report.
            violation_count = len(violations)
        else:
            violation_count = 0
    else:
        violation_count = 0
        logger.warning("Could not compute composition sums.")

    # 2. Count non-null hardness
    non_null_hardness = df['hardness_hv'].notna().sum()
    total_n = len(df)

    # 3. Count excluded records from filtered file
    excluded_count = 0
    if FILTERED_FILE.exists():
        try:
            excluded_df = pd.read_csv(FILTERED_FILE)
            excluded_count = len(excluded_df)
        except Exception as e:
            logger.warning(f"Could not read filtered records file: {e}")

    # 4. Determine threshold status
    if total_n >= target_n:
        status_str = "N>=100"
        warning = None
    elif total_n >= min_n_power:
        status_str = "50<=N<100"
        warning = None # Warning might be added later by T057, but T014 sets the flag if N < 50
    else:
        status_str = "N<50"
        warning = "N < 50"

    # 5. Write status file
    status_data = {
        "threshold_status": status_str,
        "exact_N": total_n,
        "excluded_count": excluded_count,
        "non_null_hardness_count": non_null_hardness,
        "composition_violation_count": violation_count
    }
    
    if warning:
        status_data["power_limitation_warning"] = warning

    try:
        with open(STATUS_FILE, 'w') as f:
            json.dump(status_data, f, indent=2)
        logger.info(f"Written ingestion status to {STATUS_FILE}: {status_data}")
    except Exception as e:
        logger.error(f"Failed to write status file: {e}")
        sys.exit(1)

def main():
    """Main entry point."""
    logger.info("Starting T014: Validation and Status Write")
    validate_and_write_status()
    logger.info("T014 completed.")

if __name__ == "__main__":
    main()