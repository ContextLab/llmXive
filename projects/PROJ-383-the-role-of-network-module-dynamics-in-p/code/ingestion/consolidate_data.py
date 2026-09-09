import sys
import os
import logging
import pandas as pd
import numpy as np
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRUBBED_TIMESERIES_PATH = PROJECT_ROOT / "data" / "processed" / "scrubbed_timeseries.parquet"
BEHAVIORAL_SCORES_PATH = PROJECT_ROOT / "data" / "processed" / "behavioral_scores.parquet"
OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "consolidated_data.parquet"

def load_scrubbed_timeseries() -> pd.DataFrame:
    """
    Load the scrubbed fMRI time series data.
    
    Returns:
        pd.DataFrame: Time series data with subject IDs and time points.
        
    Raises:
        FileNotFoundError: If the scrubbed timeseries file does not exist.
        ValueError: If the file is empty or missing required columns.
    """
    if not SCRUBBED_TIMESERIES_PATH.exists():
        raise FileNotFoundError(
            f"Scrubbed timeseries file not found at {SCRUBBED_TIMESERIES_PATH}. "
            "Please ensure T012b (preprocessing) has been completed."
        )
    
    df = pd.read_parquet(SCRUBBED_TIMESERIES_PATH)
    
    if df.empty:
        raise ValueError("Scrubbed timeseries file is empty.")
    
    # Expected columns: subject_id, time_point, and region-wise connectivity values
    required_cols = ['subject_id', 'time_point']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Scrubbed timeseries missing required columns: {missing_cols}")
    
    logger.info(f"Loaded scrubbed timeseries with {len(df)} rows.")
    return df

def load_behavioral_scores() -> pd.DataFrame:
    """
    Load the behavioral scores (2-back accuracy) data.
    
    Returns:
        pd.DataFrame: Behavioral scores with subject IDs and accuracy metrics.
        
    Raises:
        FileNotFoundError: If the behavioral scores file does not exist.
        ValueError: If the file is empty or missing required columns.
    """
    if not BEHAVIORAL_SCORES_PATH.exists():
        raise FileNotFoundError(
            f"Behavioral scores file not found at {BEHAVIORAL_SCORES_PATH}. "
            "Please ensure T011 (download) has been completed."
        )
    
    df = pd.read_parquet(BEHAVIORAL_SCORES_PATH)
    
    if df.empty:
        raise ValueError("Behavioral scores file is empty.")
    
    # Expected columns: subject_id, accuracy (or similar metric)
    required_cols = ['subject_id']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Behavioral scores missing required columns: {missing_cols}")
    
    logger.info(f"Loaded behavioral scores with {len(df)} rows.")
    return df

def load_motion_params() -> pd.DataFrame:
    """
    Load motion parameters if available, for reference in consolidation.
    
    Returns:
        pd.DataFrame: Motion parameters with subject IDs and mean FD.
        
    Raises:
        FileNotFoundError: If the motion parameters file does not exist.
    """
    motion_path = PROJECT_ROOT / "data" / "processed" / "motion_params.parquet"
    if not motion_path.exists():
        logger.warning(f"Motion parameters file not found at {motion_path}. "
                     "Consolidation will proceed without motion data.")
        return pd.DataFrame()
    
    df = pd.read_parquet(motion_path)
    logger.info(f"Loaded motion parameters with {len(df)} rows.")
    return df

def merge_datasets(timeseries_df: pd.DataFrame, 
                   behavioral_df: pd.DataFrame, 
                   motion_df: pd.DataFrame = None) -> pd.DataFrame:
    """
    Merge cleaned time series and behavioral scores into a consolidated dataset.
    
    The merge is performed on 'subject_id'. Only subjects present in both
    datasets are included (inner join).
    
    Args:
        timeseries_df: Scrubbed time series data.
        behavioral_df: Behavioral scores data.
        motion_df: Optional motion parameters data.
        
    Returns:
        pd.DataFrame: Consolidated dataset with subject-level features.
    """
    # Aggregate time series to subject-level features if needed
    # For now, we assume the time series is already aggregated or we just need
    # to ensure subject-level alignment. If the time series has multiple rows per subject,
    # we might need to aggregate (e.g., mean connectivity per subject).
    # However, based on the task description, we are merging "cleaned time series"
    # which might imply a subject-level summary or a long format that we keep.
    # Let's assume we need to create a subject-level summary for the time series
    # if it's in long format, or just merge if it's already subject-level.
    
    # Check if time series is in long format (multiple rows per subject)
    if timeseries_df['subject_id'].nunique() < len(timeseries_df):
        # Aggregate to subject level: mean of all time points/regions
        # This is a simplification; actual aggregation might depend on the specific
        # structure of the time series data.
        logger.info("Aggregating time series data to subject level...")
        # Drop non-numeric columns for aggregation
        numeric_cols = timeseries_df.select_dtypes(include=[np.number]).columns
        numeric_cols = [c for c in numeric_cols if c not in ['time_point']]
        
        if numeric_cols:
            subject_summary = timeseries_df.groupby('subject_id')[numeric_cols].mean().reset_index()
        else:
            # If no numeric columns, just get unique subjects
            subject_summary = timeseries_df[['subject_id']].drop_duplicates()
    else:
        subject_summary = timeseries_df.copy()
    
    # Merge with behavioral scores
    consolidated = pd.merge(
        subject_summary,
        behavioral_df,
        on='subject_id',
        how='inner'
    )
    
    # Merge with motion parameters if available
    if motion_df is not None and not motion_df.empty:
        consolidated = pd.merge(
            consolidated,
            motion_df[['subject_id', 'mean_fd']],
            on='subject_id',
            how='left'
        )
        logger.info(f"Merged with motion parameters. {consolidated['mean_fd'].isna().sum()} subjects without motion data.")
    
    logger.info(f"Consolidated dataset has {len(consolidated)} subjects.")
    return consolidated

def validate_consolidated_data(df: pd.DataFrame) -> bool:
    """
    Validate the consolidated dataset.
    
    Args:
        df: Consolidated DataFrame.
        
    Returns:
        bool: True if validation passes, False otherwise.
        
    Raises:
        ValueError: If validation fails.
    """
    if df.empty:
        raise ValueError("Consolidated dataset is empty.")
    
    if 'subject_id' not in df.columns:
        raise ValueError("Consolidated dataset missing 'subject_id' column.")
    
    # Check for NaN in critical columns
    critical_cols = ['subject_id']
    for col in critical_cols:
        if df[col].isna().any():
            raise ValueError(f"Critical column '{col}' contains NaN values.")
    
    logger.info("Consolidated data validation passed.")
    return True

def main():
    """
    Main function to run the data consolidation pipeline.
    """
    try:
        logger.info("Starting data consolidation...")
        
        # Load data
        timeseries_df = load_scrubbed_timeseries()
        behavioral_df = load_behavioral_scores()
        motion_df = load_motion_params()
        
        # Merge datasets
        consolidated_df = merge_datasets(timeseries_df, behavioral_df, motion_df)
        
        # Validate
        validate_consolidated_data(consolidated_df)
        
        # Save output
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        consolidated_df.to_parquet(OUTPUT_PATH, index=False)
        
        logger.info(f"Consolidated data saved to {OUTPUT_PATH}")
        logger.info(f"Output shape: {consolidated_df.shape}")
        logger.info(f"Columns: {list(consolidated_df.columns)}")
        
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during consolidation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
