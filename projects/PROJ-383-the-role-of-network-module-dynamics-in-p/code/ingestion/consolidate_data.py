"""
Consolidate cleaned fMRI time series and behavioral scores into a single Parquet file.

This script merges:
1. Scrubbed time series from data/processed/scrubbed_timeseries.parquet
2. Behavioral scores (2-back accuracy) from the HCP dataset
3. Subject-level motion metrics (mean FD)

Output: data/processed/consolidated_data.parquet
"""
import sys
import os
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Optional, List, Tuple

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.logging_config import setup_logging, log_subject_exclusion
from utils.memory_monitor import check_memory_limit, get_memory_usage_report
from utils.config import set_all_seeds

# Setup logging
logger = setup_logging()
set_all_seeds()

# Constants
SCRUBBED_TIMESERIES_PATH = Path("data/processed/scrubbed_timeseries.parquet")
BEHAVIORAL_DATA_PATH = Path("data/raw_behavior/behavioral_scores.parquet")
CONSOLIDATED_OUTPUT_PATH = Path("data/processed/consolidated_data.parquet")
MOTION_PARAMS_PATH = Path("data/processed/motion_params.parquet")

def load_scrubbed_timeseries() -> pd.DataFrame:
    """Load scrubbed time series data."""
    if not SCRUBBED_TIMESERIES_PATH.exists():
        raise FileNotFoundError(f"Scrubbed timeseries not found at {SCRUBBED_TIMESERIES_PATH}")
    
    logger.info(f"Loading scrubbed timeseries from {SCRUBBED_TIMESERIES_PATH}")
    df = pd.read_parquet(SCRUBBED_TIMESERIES_PATH)
    
    # Validate required columns
    required_cols = ['subject_id', 'timepoint', 'region', 'signal']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Scrubbed timeseries missing required columns: {missing}")
    
    logger.info(f"Loaded {len(df)} rows of scrubbed timeseries data")
    return df

def load_behavioral_scores() -> pd.DataFrame:
    """Load behavioral scores (2-back accuracy) from HCP dataset."""
    if not BEHAVIORAL_DATA_PATH.exists():
        # Try alternative path if behavioral data is in raw_behavior
        alt_path = Path("data/raw_behavior/2back_accuracy.csv")
        if alt_path.exists():
            logger.info(f"Loading behavioral scores from {alt_path}")
            df = pd.read_csv(alt_path)
            # Normalize column names
            df.columns = [col.lower().strip() for col in df.columns]
            if 'subject_id' not in df.columns and 'sub' in df.columns:
                df['subject_id'] = df['sub']
            return df
        raise FileNotFoundError(f"Behavioral scores not found at {BEHAVIORAL_DATA_PATH} or {alt_path}")
    
    logger.info(f"Loading behavioral scores from {BEHAVIORAL_DATA_PATH}")
    df = pd.read_parquet(BEHAVIORAL_DATA_PATH)
    
    # Normalize column names
    df.columns = [col.lower().strip() for col in df.columns]
    
    # Ensure subject_id column exists
    if 'subject_id' not in df.columns:
        if 'sub' in df.columns:
            df['subject_id'] = df['sub']
        elif 'participant_id' in df.columns:
            df['subject_id'] = df['participant_id']
        else:
            raise ValueError("Behavioral scores missing subject identifier column")
    
    logger.info(f"Loaded {len(df)} rows of behavioral scores")
    return df

def load_motion_params() -> pd.DataFrame:
    """Load motion parameters (mean FD) for each subject."""
    if MOTION_PARAMS_PATH.exists():
        logger.info(f"Loading motion parameters from {MOTION_PARAMS_PATH}")
        return pd.read_parquet(MOTION_PARAMS_PATH)
    
    # If motion params not in separate file, they might be in scrubbed timeseries
    # as a summary statistic or need to be calculated
    logger.warning("Motion parameters file not found, will attempt to derive from existing data")
    return pd.DataFrame()

def merge_datasets(
    timeseries_df: pd.DataFrame,
    behavioral_df: pd.DataFrame,
    motion_df: Optional[pd.DataFrame] = None
) -> pd.DataFrame:
    """
    Merge all datasets into a consolidated dataframe.
    
    The consolidation creates a subject-level summary that includes:
    - Subject ID
    - Behavioral score (2-back accuracy)
    - Mean FD (motion metric)
    - Number of timepoints after scrubbing
    - Number of brain regions
    
    Note: Time series data is kept separate to avoid massive file sizes.
    The consolidated file contains subject-level metadata and indices.
    """
    logger.info("Merging datasets...")
    
    # Get unique subjects from timeseries
    timeseries_subjects = timeseries_df['subject_id'].unique()
    logger.info(f"Found {len(timeseries_subjects)} subjects in timeseries data")
    
    # Filter behavioral data to only include subjects with timeseries
    merged_df = behavioral_df[behavioral_df['subject_id'].isin(timeseries_subjects)].copy()
    
    if len(merged_df) == 0:
        raise ValueError("No overlapping subjects between timeseries and behavioral data")
    
    logger.info(f"Merged with {len(merged_df)} subjects having both data types")
    
    # Calculate subject-level statistics from timeseries
    subject_stats = timeseries_df.groupby('subject_id').agg(
        n_timepoints=('timepoint', 'count'),
        n_regions=('region', 'nunique')
    ).reset_index()
    
    # Merge with behavioral data
    merged_df = merged_df.merge(subject_stats, on='subject_id', how='left')
    
    # Add motion parameters if available
    if motion_df is not None and not motion_df.empty:
        # Ensure subject_id column exists in motion_df
        if 'subject_id' not in motion_df.columns:
            if 'sub' in motion_df.columns:
                motion_df['subject_id'] = motion_df['sub']
            else:
                logger.warning("Motion parameters missing subject_id column, skipping merge")
        else:
          merged_df = merged_df.merge(
              motion_df[['subject_id', 'mean_fd']],
              on='subject_id',
              how='left'
          )
          logger.info("Merged motion parameters")
    
    # Validate final merge
    required_cols = ['subject_id', 'accuracy']  # accuracy is typical name for 2-back
    # Try to find accuracy column with different names
    accuracy_cols = [col for col in merged_df.columns if 'accuracy' in col.lower() or 'score' in col.lower() or '2back' in col.lower()]
    if accuracy_cols:
        merged_df['accuracy'] = merged_df[accuracy_cols[0]]
        logger.info(f"Using {accuracy_cols[0]} as accuracy column")
    else:
        # If no accuracy column found, create a placeholder (should not happen with real data)
        logger.warning("No accuracy column found in behavioral data, creating placeholder")
        merged_df['accuracy'] = np.nan
    
    # Drop duplicates and sort
    merged_df = merged_df.drop_duplicates(subset=['subject_id']).sort_values('subject_id')
    
    logger.info(f"Final consolidated dataset has {len(merged_df)} subjects")
    return merged_df

def validate_consolidated_data(df: pd.DataFrame) -> bool:
    """Validate the consolidated dataset meets requirements."""
    if df.empty:
        logger.error("Consolidated dataset is empty")
        return False
    
    if 'subject_id' not in df.columns:
        logger.error("Consolidated dataset missing subject_id column")
        return False
    
    if 'accuracy' not in df.columns:
        logger.error("Consolidated dataset missing accuracy column")
        return False
    
    # Check for NaN in critical columns
    if df['subject_id'].isna().any():
        logger.error("Consolidated dataset contains NaN subject_ids")
        return False
    
    logger.info("Consolidated dataset validation passed")
    return True

def main():
    """Main entry point for data consolidation."""
    logger.info("Starting data consolidation process")
    
    # Check memory before processing
    check_memory_limit()
    
    try:
        # Load all data sources
        timeseries_df = load_scrubbed_timeseries()
        behavioral_df = load_behavioral_scores()
        motion_df = load_motion_params()
        
        # Merge datasets
        consolidated_df = merge_datasets(timeseries_df, behavioral_df, motion_df)
        
        # Validate output
        if not validate_consolidated_data(consolidated_df):
            raise ValueError("Consolidated data validation failed")
        
        # Ensure output directory exists
        CONSOLIDATED_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        # Save consolidated data
        logger.info(f"Saving consolidated data to {CONSOLIDATED_OUTPUT_PATH}")
        consolidated_df.to_parquet(
            CONSOLIDATED_OUTPUT_PATH,
            index=False,
            compression='snappy'
        )
        
        # Verify file was created
        if not CONSOLIDATED_OUTPUT_PATH.exists():
            raise RuntimeError(f"Failed to create output file: {CONSOLIDATED_OUTPUT_PATH}")
        
        file_size_mb = CONSOLIDATED_OUTPUT_PATH.stat().st_size / (1024 * 1024)
        logger.info(f"Successfully saved consolidated data ({file_size_mb:.2f} MB)")
        
        # Log final memory usage
        memory_report = get_memory_usage_report()
        logger.info(f"Final memory usage: {memory_report}")
        
        print(f"Consolidated data saved to: {CONSOLIDATED_OUTPUT_PATH}")
        print(f"Subjects included: {len(consolidated_df)}")
        print(f"Columns: {list(consolidated_df.columns)}")
        
    except Exception as e:
        logger.error(f"Consolidation failed: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
