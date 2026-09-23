"""
T014: Implement validation reporting logic.
Checks for non-null hardness, complete composition, and writes ingestion status.
This script reads the cleaned data produced by T013, validates it against the
composition sum threshold, counts valid records, and writes the status file
required by downstream tasks (T016b, T031c, etc.).
"""
import os
import sys
import json
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from config import (
    get_data_processed_dir, 
    get_composition_sum_threshold, 
    get_min_n_for_power, 
    get_target_n
)
from utils.logging_config import get_logger

logger = get_logger(__name__)

PROCESSED_DIR = get_data_processed_dir()
CLEANED_FILE = PROCESSED_DIR / "solder_hardness_cleaned.csv"
EXCLUDED_FILE = PROCESSED_DIR / "excluded_records.csv"
STATUS_FILE = PROCESSED_DIR / ".ingestion_status.json"

def validate_and_write_status():
    """
    1. Read cleaned data.
    2. Verify composition sums (should all be >= threshold).
    3. Count non-null hardness.
    4. Read excluded records count.
    5. Write .ingestion_status.json.
    """
    if not CLEANED_FILE.exists():
        logger.error(f"Cleaned data file not found: {CLEANED_FILE}")
        logger.error("T013 (cleaner.py) must be run successfully before T014.")
        sys.exit(1)

    df = pd.read_csv(CLEANED_FILE)
    threshold = get_composition_sum_threshold()
    min_n_power = get_min_n_for_power()
    target_n = get_target_n()

    logger.info(f"Validating {len(df)} records in {CLEANED_FILE}")
    logger.info(f"Threshold: {threshold}, Min N for Power: {min_n_power}, Target N: {target_n}")

    # 1. Calculate composition sums explicitly to confirm validity
    # Identify columns that are likely elemental compositions.
    # We assume the cleaned CSV has columns for elements (e.g., 'Sn', 'Ag', 'Cu', 'Bi', 'In')
    # and potentially 'hardness_hv', 'measurement_temp_c', 'alloy_family', etc.
    # Strategy: Select numeric columns, exclude known non-composition columns.
    
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    
    # Columns to definitely exclude from composition sum
    exclude_cols = ['hardness_hv', 'measurement_temp_c', 'composition_sum'] 
    
    composition_cols = [c for c in numeric_cols if c not in exclude_cols]
    
    if not composition_cols:
        logger.warning("No composition columns found. Attempting to infer from all numeric except hardness.")
        composition_cols = [c for c in numeric_cols if c != 'hardness_hv']
    
    violation_count = 0
    if composition_cols:
        # Calculate sum
        df['_temp_composition_sum'] = df[composition_cols].sum(axis=1)
        
        # Check for violations (should ideally be 0 if T013 worked correctly)
        violations = df[df['_temp_composition_sum'] < threshold]
        violation_count = len(violations)
        
        if violation_count > 0:
            logger.warning(f"Found {violation_count} records with composition sum < {threshold}. "
                           "These should have been filtered in T013. Flagging for review.")
        
        # Drop temp column
        df.drop(columns=['_temp_composition_sum'], inplace=True)
    else:
        logger.warning("Could not compute composition sums. No eligible columns found.")

    # 2. Count non-null hardness
    non_null_hardness = int(df['hardness_hv'].notna().sum())
    total_n = len(df)

    # 3. Count excluded records from excluded file
    excluded_count = 0
    if EXCLUDED_FILE.exists():
        try:
            excluded_df = pd.read_csv(EXCLUDED_FILE)
            excluded_count = len(excluded_df)
            logger.info(f"Found {excluded_count} excluded records in {EXCLUDED_FILE}")
        except Exception as e:
            logger.warning(f"Could not read excluded records file: {e}")
    else:
        logger.info(f"Excluded records file not found ({EXCLUDED_FILE}). Assuming 0 excluded.")

    # 4. Determine threshold status and warnings
    # Logic from T014 description:
    # - If N < 50: severe warning, power_limitation_warning = 'N < 50'
    # - If 50 <= N < 100: proceed with flag
    # - If N >= 100: success
    
    if total_n >= target_n:
        status_str = "N>=100"
        warning = None
    elif total_n >= min_n_power:
        status_str = "50<=N<100"
        warning = None # No severe warning, but might be noted in report
    else:
        status_str = "N<50"
        warning = "N < 50"

    # 5. Construct status data
    status_data: Dict[str, Any] = {
        "threshold_status": status_str,
        "exact_N": total_n,
        "excluded_count": excluded_count,
        "non_null_hardness_count": non_null_hardness,
        "composition_violation_count": violation_count
    }
    
    if warning:
        status_data["power_limitation_warning"] = warning

    # 6. Write status file
    try:
        with open(STATUS_FILE, 'w') as f:
            json.dump(status_data, f, indent=2)
        logger.info(f"Written ingestion status to {STATUS_FILE}")
        logger.info(f"Status details: {status_data}")
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