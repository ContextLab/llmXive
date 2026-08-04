"""
Task T012d: MMSE Exclusion (Primary)

Implements the exclusion of records where MMSE < 24.
This task depends on T013b (MMSE Flag validation).

It reads the raw dataset (or the intermediate filtered dataset if T011/T012a/b ran first),
checks for the existence of the 'MMSE' column (validated by T013b),
filters out records with MMSE < 24, and returns the count of excluded records.

The exclusion count is written to the shared state (exclusion_log.json) 
to be aggregated by T012c.
"""
import os
import json
import logging
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any

# Import shared utilities and config
from utils import setup_logging, log_info, log_warning, log_error
from config import get_config, get_mmse_threshold, get_env_bool

# Setup logging
logger = setup_logging("T012d_MMSE_Exclusion")

def load_intermediate_dataset(raw_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Loads the dataset. 
    In this pipeline, T011 and T012a/b might have already filtered the data.
    We attempt to load the most recent intermediate file, or the raw file.
    """
    config = get_config()
    data_dir = Path(config.get('paths', {}).get('raw', 'data/raw'))
    processed_dir = Path(config.get('paths', {}).get('processed', 'data/processed'))
    
    # Priority: Check for an intermediate file created by previous exclusion steps (T011/T012a/b)
    # If T011/T012a/b haven't run or didn't create a specific intermediate, we load raw.
    # For robustness, we look for 'raw_data_filtered.csv' or similar if it exists.
    # However, based on the task list, T010a fetches to raw, T011 filters. 
    # If T011 created 'data/processed/temp_filtered.csv', we use that.
    # If not, we load from raw.
    
    # Let's assume T011 might have written to a temp location or we just load raw and filter sequentially.
    # To be safe and stateless for this specific task, we load the raw data and apply ALL filters 
    # if previous state files don't exist, OR we load the state of the pipeline.
    
    # Strategy: 
    # 1. Check if 'data/processed/temp_pre_mmse.csv' exists (output of T011/T012a/b).
    # 2. If not, load 'data/raw/dataset.csv' (or whatever T010a produced).
    
    temp_path = processed_dir / "temp_pre_mmse.csv"
    if temp_path.exists():
        logger.info(f"Loading intermediate dataset from {temp_path}")
        return pd.read_csv(temp_path)
    
    # Fallback: Load raw data. 
    # Note: In a real pipeline, T011/T012a/b should have written their output.
    # If this task runs in isolation (as a unit), we load raw and apply age/score filters too?
    # The task says "If MMSE column exists... exclude records". It implies we are operating on the dataset 
    # that has already passed age/score checks.
    # If the intermediate file is missing, we must load raw and assume we need to re-apply previous filters 
    # OR we just load raw and warn that previous steps might be missing.
    # Given the strict dependency "Depends on T013b" (which checks column) and T012a/b (age/score),
    # we assume the data passed to this function is the result of those steps.
    # If the intermediate file is missing, we load raw and warn.
    
    raw_files = list(data_dir.glob("*.csv"))
    if not raw_files:
        raise FileNotFoundError("No raw dataset found in data/raw/ and no intermediate temp file found.")
    
    # Assume the first csv is the raw dataset
    raw_path = raw_files[0]
    logger.warning(f"Intermediate file not found. Loading raw data from {raw_path}. "
                   "Note: Age and Score exclusions (T012a/b) have NOT been applied yet in this run.")
    return pd.read_csv(raw_path)

def filter_mmse(df: pd.DataFrame, threshold: Optional[int] = None) -> tuple[pd.DataFrame, int]:
    """
    Filters the dataframe to exclude records where MMSE < threshold.
    
    Args:
        df: Input dataframe.
        threshold: MMSE threshold (default 24).
        
    Returns:
        Tuple of (filtered_df, excluded_count)
    """
    if threshold is None:
        threshold = get_mmse_threshold()
        
    # Check if MMSE column exists
    if 'MMSE' not in df.columns:
        log_warning("ERR_MMSE_MISSING: 'MMSE' column not found in dataset. No MMSE exclusion performed.")
        return df, 0
    
    # Handle non-numeric MMSE values if any (coerce to NaN)
    df['MMSE'] = pd.to_numeric(df['MMSE'], errors='coerce')
    
    # Filter: Keep rows where MMSE >= threshold OR MMSE is NaN (if we treat missing as not excluded? 
    # Task says "exclude records where MMSE < 24". If MMSE is missing, it's not < 24, so we keep?
    # Usually in clinical studies, missing MMSE might be excluded separately, but strictly following "MMSE < 24":
    # We exclude only those explicitly < 24.
    
    excluded_mask = df['MMSE'] < threshold
    excluded_count = excluded_mask.sum()
    
    filtered_df = df[~excluded_mask].copy()
    
    log_info(f"MMSE Exclusion: Excluded {excluded_count} records with MMSE < {threshold}.")
    log_info(f"Remaining records: {len(filtered_df)}")
    
    return filtered_df, int(excluded_count)

def save_exclusion_count(excluded_count: int, exclusion_log_path: Path) -> None:
    """
    Updates the exclusion log with the MMSE exclusion count.
    """
    log_info(f"Updating exclusion log at {exclusion_log_path}")
    
    # Load existing log if it exists
    if exclusion_log_path.exists():
        with open(exclusion_log_path, 'r') as f:
            log_data = json.load(f)
    else:
        log_data = {}
    
    # Update MMSE count
    log_data['ERR_MMSE_IMPAIRED'] = excluded_count
    
    # Save back
    with open(exclusion_log_path, 'w') as f:
        json.dump(log_data, f, indent=2)
    
    log_info(f"Exclusion log updated: ERR_MMSE_IMPAIRED = {excluded_count}")

def main():
    """
    Main entry point for Task T012d.
    """
    config = get_config()
    processed_dir = Path(config.get('paths', {}).get('processed', 'data/processed'))
    exclusion_log_path = processed_dir / "exclusion_log.json"
    output_intermediate_path = processed_dir / "temp_pre_mmse.csv"
    
    # Ensure directories exist
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # 1. Load Data
        df = load_intermediate_dataset()
        original_count = len(df)
        
        # 2. Check MMSE Flag (T013b dependency)
        # We assume T013b ran and set a config or we just check the column existence here.
        # The task says "If MMSE column exists (checked by T013b)".
        # We perform the check again to be safe.
        if 'MMSE' not in df.columns:
            log_warning("T013b check failed or MMSE column missing. Skipping MMSE exclusion.")
            # We still write 0 to the log to maintain state consistency
            save_exclusion_count(0, exclusion_log_path)
            # Save the unchanged data as intermediate for next step
            df.to_csv(output_intermediate_path, index=False)
            return
        
        # 3. Filter MMSE
        threshold = get_mmse_threshold()
        filtered_df, excluded_count = filter_mmse(df, threshold)
        
        # 4. Save Exclusion Count to Shared State
        save_exclusion_count(excluded_count, exclusion_log_path)
        
        # 5. Save Intermediate Dataset for T012c/T014a
        filtered_df.to_csv(output_intermediate_path, index=False)
        log_info(f"Intermediate dataset saved to {output_intermediate_path}")
        
        log_info("Task T012d completed successfully.")
        
    except Exception as e:
        log_error(f"Task T012d failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()