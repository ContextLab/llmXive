import os
import json
import logging
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any

from config import get_config, get_mmse_threshold
from utils import setup_logging, log_info, log_warning, log_error, get_timestamp

# Configure logging
setup_logging()
logger = logging.getLogger(__name__)

def load_score_filtered_dataset() -> pd.DataFrame:
    """
    Loads the dataset filtered by age and score (T012b output).
    """
    config = get_config()
    input_path = config['paths']['processed'] / 'cleaned_score_filtered.csv'
    
    if not input_path.exists():
        raise FileNotFoundError(f"Required input file not found: {input_path}. "
                                "Ensure T012b has been completed successfully.")
    
    logger.info(f"Loading score filtered dataset from {input_path}")
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} records from score filtered dataset")
    return df

def load_mmse_flag() -> bool:
    """
    Reads the MMSE flag produced by T012d.
    Returns True if MMSE column exists and has non-null values, False otherwise.
    """
    config = get_config()
    flag_path = config['paths']['processed'] / 'mmse_flag.json'
    
    if not flag_path.exists():
        raise FileNotFoundError(f"MMSE flag file not found: {flag_path}. "
                                "Ensure T012d has been completed successfully.")
    
    with open(flag_path, 'r') as f:
        data = json.load(f)
    
    has_mmse = data.get('has_mmse', False)
    logger.info(f"Read MMSE flag: has_mmse={has_mmse}")
    return has_mmse

def filter_mmse(df: pd.DataFrame, threshold: int = 24) -> pd.DataFrame:
    """
    Filters the dataframe for MMSE >= threshold.
    If 'MMSE' column is missing, returns the dataframe unchanged (should not happen if has_mmse=True).
    """
    if 'MMSE' not in df.columns:
        log_warning("MMSE column missing in dataframe during filtering, returning unfiltered data.")
        return df
    
    original_count = len(df)
    filtered_df = df[df['MMSE'] >= threshold].copy()
    excluded_count = original_count - len(filtered_df)
    
    log_info(f"Filtered MMSE >= {threshold}: kept {len(filtered_df)}, excluded {excluded_count}")
    return filtered_df, excluded_count

def save_cleaned_dataset(df: pd.DataFrame, output_path: Path) -> None:
    """
    Saves the final cleaned dataset (with MMSE exclusion if applicable).
    """
    df.to_csv(output_path, index=False)
    log_info(f"Saved cleaned dataset to {output_path} with {len(df)} records")

def save_no_mmse_dataset(df: pd.DataFrame, output_path: Path) -> None:
    """
    Saves the dataset without MMSE exclusion (for robustness analysis).
    This is a copy of the score-filtered dataset.
    """
    df.to_csv(output_path, index=False)
    log_info(f"Saved no-MMSE dataset to {output_path} with {len(df)} records")

def update_exclusion_counts(exclusion_counts: Dict[str, Any], key: str, count: int) -> Dict[str, Any]:
    """
    Updates the exclusion counts dictionary.
    """
    exclusion_counts[key] = count
    return exclusion_counts

def save_exclusion_counts(exclusion_counts: Dict[str, Any], output_path: Path) -> None:
    """
    Saves the exclusion counts to a JSON file.
    """
    with open(output_path, 'w') as f:
        json.dump(exclusion_counts, f, indent=2)
    log_info(f"Saved exclusion counts to {output_path}")

def main():
    """
    T012e: MMSE EXCLUSION AND ROBUSTNESS PREP
    
    Logic:
    1. Read has_mmse from data/processed/mmse_flag.json (T012d output).
    2. Load data/processed/cleaned_score_filtered.csv (T012b output).
    3. If has_mmse is True:
       - Filter for MMSE >= 24 -> data/processed/cleaned_dataset.csv (Primary)
    4. If has_mmse is False:
       - Copy score_filtered -> data/processed/cleaned_dataset.csv (Primary)
    5. ALWAYS: Copy score_filtered -> data/processed/cleaned_dataset_no_mmse.csv (Robustness)
    6. Update and save exclusion_counts.json.
    """
    logger.info("Starting T012e: MMSE Exclusion and Robustness Prep")
    config = get_config()
    mmse_threshold = get_mmse_threshold()
    
    # 1. Load MMSE Flag
    try:
        has_mmse = load_mmse_flag()
    except FileNotFoundError as e:
        log_error(str(e))
        raise

    # 2. Load Score Filtered Dataset
    try:
        df_score_filtered = load_score_filtered_dataset()
    except FileNotFoundError as e:
        log_error(str(e))
        raise

    # Initialize exclusion counts (load existing if possible, else start fresh)
    exclusion_counts_path = config['paths']['processed'] / 'exclusion_counts.json'
    exclusion_counts = {}
    if exclusion_counts_path.exists():
        try:
            with open(exclusion_counts_path, 'r') as f:
                exclusion_counts = json.load(f)
        except json.JSONDecodeError:
            exclusion_counts = {}

    # 3. Process based on has_mmse flag
    if has_mmse:
        log_info("MMSE data present. Applying MMSE >= 24 filter.")
        df_primary, mmse_excluded_count = filter_mmse(df_score_filtered, mmse_threshold)
        
        # Save Primary Dataset (with MMSE)
        primary_path = config['paths']['processed'] / 'cleaned_dataset.csv'
        save_cleaned_dataset(df_primary, primary_path)
        
        # Update exclusion counts
        exclusion_counts['ERR_MMSE_IMPAIRED'] = mmse_excluded_count
    else:
        log_info("MMSE data not present or all null. Skipping MMSE filter.")
        df_primary = df_score_filtered.copy()
        
        # Save Primary Dataset (same as score filtered)
        primary_path = config['paths']['processed'] / 'cleaned_dataset.csv'
        save_cleaned_dataset(df_primary, primary_path)
        
        # No MMSE exclusion to record
        exclusion_counts['ERR_MMSE_IMPAIRED'] = 0

    # 4. ALWAYS Generate Robustness Dataset (copy of score filtered)
    robustness_path = config['paths']['processed'] / 'cleaned_dataset_no_mmse.csv'
    save_no_mmse_dataset(df_score_filtered, robustness_path)

    # 5. Save Updated Exclusion Counts
    save_exclusion_counts(exclusion_counts, exclusion_counts_path)

    logger.info("T012e completed successfully.")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
