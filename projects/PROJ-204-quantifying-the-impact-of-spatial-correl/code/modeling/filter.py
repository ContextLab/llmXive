"""
Unified Sample Filtering Module for T034.

Consumes validation_flag (from T016) and depth_flag (from T023)
to filter the pre-filter dataset (T014c) and produce the primary_analysis_dataset.
"""
import os
import logging
import pandas as pd
from pathlib import Path
from typing import Optional, Tuple, List

from utils.config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for flag values (assumed based on typical validation logic)
VALID_FLAG_VALUE = 0  # 0 indicates valid/matched
DEPTH_FLAG_VALUE = 0  # 0 indicates no depth conflict

def load_pre_filter_dataset(input_path: str) -> pd.DataFrame:
    """
    Loads the unified dataset produced by T014c.
    
    Args:
        input_path: Path to data/processed/unified_dataset.csv
        
    Returns:
        DataFrame containing the pre-filter dataset.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If required columns are missing.
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input dataset not found at {input_path}. "
                                "Ensure T014c has completed successfully.")
    
    df = pd.read_csv(path)
    
    required_cols = ['sample_id', 'validation_flag', 'depth_flag']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in {input_path}: {missing_cols}")
        
    return df

def filter_samples(df: pd.DataFrame) -> Tuple[pd.DataFrame, int, int, int]:
    """
    Filters the dataset based on validation_flag and depth_flag.
    
    Logic:
    - Keep rows where validation_flag == VALID_FLAG_VALUE AND depth_flag == DEPTH_FLAG_VALUE.
    - Drop rows where either flag indicates a failure/conflict.
    
    Args:
        df: Input DataFrame with validation flags.
        
    Returns:
        Tuple of (filtered_df, count_kept, count_dropped_validation, count_dropped_depth)
    """
    logger.info(f"Starting filtering on dataset with {len(df)} samples.")
    
    # Initial counts for logging
    total = len(df)
    
    # Filter for valid samples
    # Assuming flags are numeric: 0 = valid/pass, >0 = invalid/fail
    # If flags are strings, comparison logic would need adjustment, 
    # but typical pipeline flags are integers.
    mask = (df['validation_flag'] == VALID_FLAG_VALUE) & (df['depth_flag'] == DEPTH_FLAG_VALUE)
    
    filtered_df = df[mask].copy()
    
    dropped_total = total - len(filtered_df)
    dropped_validation = len(df[df['validation_flag'] != VALID_FLAG_VALUE])
    dropped_depth = len(df[(df['validation_flag'] == VALID_FLAG_VALUE) & (df['depth_flag'] != DEPTH_FLAG_VALUE)])
    
    logger.info(f"Filtering complete. Kept: {len(filtered_df)}, Dropped (validation): {dropped_validation}, "
                f"Dropped (depth): {dropped_depth}, Total dropped: {dropped_total}")
    
    return filtered_df, len(filtered_df), dropped_validation, dropped_depth

def write_filtered_dataset(df: pd.DataFrame, output_path: str) -> None:
    """
    Writes the filtered DataFrame to the specified output path.
    
    Args:
        df: The filtered DataFrame.
        output_path: Path to save the CSV (e.g., data/processed/primary_analysis_dataset.csv).
    """
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    logger.info(f"Primary analysis dataset written to {output_path}")

def main() -> None:
    """
    Main entry point for T034 execution.
    
    Reads config for paths, loads T014c output, filters, and writes T034 output.
    """
    config = get_config()
    
    # Determine paths from config or defaults
    input_path = config.get('paths', {}).get('pre_filter_dataset', 'data/processed/unified_dataset.csv')
    output_path = config.get('paths', {}).get('primary_analysis_dataset', 'data/processed/primary_analysis_dataset.csv')
    
    logger.info(f"Loading pre-filter dataset from: {input_path}")
    try:
        df_raw = load_pre_filter_dataset(input_path)
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Failed to load input dataset: {e}")
        raise
    
    logger.info("Applying unified sample filters...")
    df_filtered, kept, dropped_val, dropped_dep = filter_samples(df_raw)
    
    if len(df_filtered) == 0:
        logger.warning("Resulting primary analysis dataset is empty! Check validation flags in source data.")
    
    logger.info(f"Writing filtered dataset to: {output_path}")
    write_filtered_dataset(df_filtered, output_path)
    
    logger.info("T034 Unified Sample Filtering completed successfully.")

if __name__ == "__main__":
    main()
