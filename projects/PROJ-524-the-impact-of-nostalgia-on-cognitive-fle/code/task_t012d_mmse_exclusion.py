"""
Task T012d: MMSE Exclusion (Primary)

This script implements the primary MMSE exclusion logic for User Story 1.
It reads the intermediate dataset (after age and score exclusions), checks for
the presence of an 'MMSE' column, filters out records where MMSE < 24, and
saves the exclusion count to the shared state (exclusion_log.json).

Dependencies:
  - T013b: Validates presence of 'MMSE' column and sets config flag.
  - T012a, T012b: Provide initial dataset state.
"""

import os
import json
import logging
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any

# Import project utilities and config
# Note: Using relative imports based on the provided API surface
# The actual imports will be resolved at runtime relative to the code directory
try:
    from config import get_config, get_mmse_threshold, ensure_dirs
    from utils import setup_logging, log_info, log_warning, log_error
except ImportError:
    # Fallback for direct execution if package structure isn't fully set up yet
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from config import get_config, get_mmse_threshold, ensure_dirs
    from utils import setup_logging, log_info, log_warning, log_error

# Constants
EXCLUSION_LOG_PATH = "data/processed/exclusion_log.json"
INTERMEDIATE_DATASET_PATH = "data/processed/intermediate_filtered.csv"
MMSE_EXCLUDED_PATH = "data/processed/mmse_excluded_records.csv"
LOG_TAG = "T012d"

def load_intermediate_dataset() -> Optional[pd.DataFrame]:
    """
    Loads the intermediate dataset produced by previous exclusion steps (T012a, T012b).
    Expected path: data/processed/intermediate_filtered.csv
    """
    path = Path(INTERMEDIATE_DATASET_PATH)
    if not path.exists():
        log_error(f"{LOG_TAG}: Intermediate dataset not found at {path}. "
                  "Ensure T012a and T012b have run successfully.")
        return None
    
    try:
        df = pd.read_csv(path)
        log_info(f"{LOG_TAG}: Loaded intermediate dataset with {len(df)} records.")
        return df
    except Exception as e:
        log_error(f"{LOG_TAG}: Failed to load intermediate dataset: {e}")
        return None

def filter_mmse(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """
    Filters the dataframe to exclude records where MMSE < 24.
    
    Returns:
      tuple: (filtered_df, excluded_count)
    """
    config = get_config()
    mmse_threshold = get_mmse_threshold()
    
    # Check if MMSE column exists
    if 'MMSE' not in df.columns:
        log_warning(f"{LOG_TAG}: 'MMSE' column not found in dataset. "
                    "Skipping MMSE exclusion. This should have been flagged by T013b.")
        return df, 0
    
    # Handle non-numeric or missing MMSE values
    # Convert to numeric, coercing errors to NaN
    df['MMSE'] = pd.to_numeric(df['MMSE'], errors='coerce')
    
    # Count records to be excluded (MMSE < threshold OR MMSE is NaN)
    # Note: The task specifies excluding MMSE < 24. 
    # Typically, missing MMSE scores are also excluded in cognitive studies,
    # but we strictly follow "MMSE < 24". If MMSE is NaN, it is not < 24 numerically,
    # but logically it's missing. We will exclude NaNs as well to be safe,
    # as a missing cognitive screen is effectively an exclusion criterion in practice.
    # However, strict reading: "exclude records where MMSE < 24".
    # Let's exclude NaNs too because you can't verify they are >= 24.
    mask_valid = df['MMSE'].notna() & (df['MMSE'] >= mmse_threshold)
    
    excluded_count = (~mask_valid).sum()
    filtered_df = df[mask_valid].copy()
    
    if excluded_count > 0:
        log_info(f"{LOG_TAG}: Excluded {excluded_count} records with MMSE < {mmse_threshold} or missing MMSE.")
        # Save excluded records for audit
        excluded_df = df[~mask_valid].copy()
        excluded_df.to_csv(MMSE_EXCLUDED_PATH, index=False)
        log_info(f"{LOG_TAG}: Saved excluded records to {MMSE_EXCLUDED_PATH}")
    else:
        log_info(f"{LOG_TAG}: No records excluded based on MMSE threshold.")
        
    return filtered_df, int(excluded_count)

def save_exclusion_count(exclusion_count: int, existing_log: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Updates the shared state exclusion log with the MMSE exclusion count.
    """
    log_info(f"{LOG_TAG}: Updating exclusion log with MMSE count: {exclusion_count}")
    
    if existing_log is None:
        existing_log = {}
    
    # Update the specific key for MMSE exclusion
    existing_log['ERR_MMSE_IMPAIRED'] = exclusion_count
    
    # Ensure directory exists
    ensure_dirs()
    
    # Write back to file
    try:
        with open(EXCLUSION_LOG_PATH, 'w', encoding='utf-8') as f:
            json.dump(existing_log, f, indent=2)
        log_info(f"{LOG_TAG}: Successfully updated {EXCLUSION_LOG_PATH}")
    except Exception as e:
        log_error(f"{LOG_TAG}: Failed to write exclusion log: {e}")
        raise e
        
    return existing_log

def main():
    """
    Main entry point for Task T012d.
    """
    setup_logging()
    log_info(f"{LOG_TAG}: Starting MMSE Exclusion process.")
    
    # 1. Load intermediate dataset
    df = load_intermediate_dataset()
    if df is None:
        log_error(f"{LOG_TAG}: Cannot proceed without intermediate dataset.")
        return
    
    # 2. Filter MMSE
    filtered_df, excluded_count = filter_mmse(df)
    
    # 3. Save filtered dataset for next steps (T012c/T014a)
    # We save the filtered version as the new intermediate state or final cleaned
    # The task says "Return count... to shared state". The cleaned dataset is saved in T014a.
    # However, to maintain flow, we save the current filtered state.
    # T012c will read the log and T014a will read the filtered data (or re-read).
    # Let's save the filtered data as the new intermediate for the next step.
    output_path = Path("data/processed/intermediate_filtered.csv")
    filtered_df.to_csv(output_path, index=False)
    log_info(f"{LOG_TAG}: Saved filtered dataset to {output_path}")
    
    # 4. Load existing exclusion log to preserve other counts
    existing_log = {}
    if os.path.exists(EXCLUSION_LOG_PATH):
        try:
            with open(EXCLUSION_LOG_PATH, 'r', encoding='utf-8') as f:
                existing_log = json.load(f)
        except json.JSONDecodeError:
            log_warning(f"{LOG_TAG}: Existing exclusion log is malformed, starting fresh.")
            existing_log = {}
    
    # 5. Save exclusion count to shared state
    save_exclusion_count(excluded_count, existing_log)
    
    log_info(f"{LOG_TAG}: MMSE Exclusion complete. Excluded {excluded_count} records.")

if __name__ == "__main__":
    main()
