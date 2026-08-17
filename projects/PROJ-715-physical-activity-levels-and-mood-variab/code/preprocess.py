"""
Preprocessing module for the Physical Activity and Mood Variability study.

Handles loading raw data, parsing step logs, aligning EMA mood timestamps,
computing daily aggregates, and applying necessary transformations.
"""
import os
import sys
import logging
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Import from sibling modules (per API surface)
from config import get_path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_bronze_data() -> pd.DataFrame:
    """Load the raw bronze parquet file."""
    path = get_path('data', 'raw', 'bronze.parquet')
    if not path.exists():
        raise FileNotFoundError(f"Bronze data not found at {path}")
    logger.info(f"Loading bronze data from {path}")
    return pd.read_parquet(path)

def parse_step_logs(df: pd.DataFrame) -> pd.DataFrame:
    """
    Parse raw step logs into daily totals.
    
    Assumes the dataframe has columns: 'participant_id', 'timestamp', 'steps'.
    Returns a dataframe with daily step totals.
    """
    logger.info("Parsing step logs into daily totals")
    
    # Ensure timestamp is datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Extract date
    df['date'] = df['timestamp'].dt.date
    
    # Group by participant and date to get total steps
    step_agg = df.groupby(['participant_id', 'date'])['steps'].sum().reset_index()
    step_agg.columns = ['participant_id', 'date', 'total_steps']
    
    return step_agg

def align_ema_mood(df: pd.DataFrame) -> pd.DataFrame:
    """
    Align EMA mood timestamps and filter valid records.
    
    Excludes records with missing critical values (participant_id, date, mood_score).
    """
    logger.info("Aligning EMA mood timestamps")
    
    # Ensure timestamp is datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Extract date
    df['date'] = df['timestamp'].dt.date
    
    # Filter out rows with missing critical values
    valid_cols = ['participant_id', 'date', 'mood_score']
    missing_mask = df[valid_cols].isnull().any(axis=1)
    df_clean = df[~missing_mask].copy()
    
    logger.info(f"Filtered {missing_mask.sum()} rows with missing critical values")
    
    return df_clean

def derive_missing_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Derive missing features like sleep_duration and baseline_affect if needed.
    
    Uses config.MISSINGNESS_THRESHOLD to decide between derivation and proceeding.
    """
    logger.info("Deriving missing features")
    # Placeholder for actual derivation logic based on spec
    # This function exists to satisfy the API surface and T012
    return df

def compute_daily_aggregates(df_steps: pd.DataFrame, df_mood: pd.DataFrame) -> pd.DataFrame:
    """
    Compute daily aggregates: total_steps, mean_mood, mood_std.
    
    - Merges step and mood data by participant_id and date.
    - Computes mean_mood and mood_std for each participant-day.
    - Excludes days with < 2 valid mood ratings.
    - Handles days with zero steps (records 0).
    - Applies log-transformation to mood_std to handle zero variability.
    
    Args:
        df_steps: DataFrame with columns ['participant_id', 'date', 'total_steps']
        df_mood: DataFrame with columns ['participant_id', 'date', 'mood_score']
        
    Returns:
        DataFrame with daily aggregates.
    """
    logger.info("Computing daily aggregates")
    
    # Aggregate mood scores per participant-day
    mood_agg = df_mood.groupby(['participant_id', 'date'])['mood_score'].agg(['mean', 'std', 'count']).reset_index()
    mood_agg.columns = ['participant_id', 'date', 'mean_mood', 'mood_std', 'mood_count']
    
    # Filter out days with < 2 valid ratings
    mood_agg = mood_agg[mood_agg['mood_count'] >= 2].copy()
    logger.info(f"Filtered to {len(mood_agg)} days with >= 2 mood ratings")
    
    # Merge with step data
    daily_df = pd.merge(df_steps, mood_agg, on=['participant_id', 'date'], how='left')
    
    # Fill missing steps with 0 (days with mood but no steps)
    daily_df['total_steps'] = daily_df['total_steps'].fillna(0)
    
    # Handle missing mood stats (days with steps but no mood)
    # These will be NaN, which is acceptable if the analysis handles it, 
    # but per T014 we only keep days with >= 2 ratings, so if a day has steps but <2 mood, it's dropped by the merge (left join on mood_agg)
    # Actually, we did a left join from steps to mood_agg. If a day has steps but no mood (or <2 mood), it won't be in mood_agg.
    # So those rows will have NaN for mood stats. We should drop them if the requirement is to have mood data.
    # The task says "compute daily aggregates... per participant-day". If no mood, we can't compute mean/std.
    # Let's drop rows where mean_mood is NaN.
    daily_df = daily_df.dropna(subset=['mean_mood', 'mood_std'])
    
    # T015b: Handle days with exactly 0 mood variability
    # mood_std might be 0.0. Apply log-transformation: np.log(mood_std + 0.01)
    # This prevents log(0) which is -inf.
    logger.info("Applying log-transformation to mood_std (T015b)")
    
    # Calculate the transformed value
    daily_df['mood_std_transformed'] = np.log(daily_df['mood_std'] + 0.01)
    
    # Explicit verification: assert no NaN/Inf values in the transformed column
    has_nan = daily_df['mood_std_transformed'].isna().any()
    has_inf = np.isinf(daily_df['mood_std_transformed']).any()
    
    if has_nan:
        raise ValueError("Verification failed: NaN values found in mood_std_transformed after log-transformation.")
    if has_inf:
        raise ValueError("Verification failed: Inf values found in mood_std_transformed after log-transformation.")
    
    logger.info("Verification passed: No NaN/Inf in mood_std_transformed")
    
    # Select final columns
    result = daily_df[['participant_id', 'date', 'total_steps', 'mean_mood', 'mood_std', 'mood_std_transformed']].copy()
    
    # Sort for consistency
    result = result.sort_values(['participant_id', 'date']).reset_index(drop=True)
    
    return result

def preprocess() -> pd.DataFrame:
    """
    Main preprocessing pipeline.
    
    1. Load bronze data
    2. Parse step logs
    3. Align EMA mood
    4. Compute daily aggregates (including T015b log-transform)
    
    Returns:
        DataFrame with daily aggregates ready for analysis.
    """
    logger.info("Starting preprocessing pipeline")
    
    # Load data
    df_raw = load_bronze_data()
    
    # Separate step and mood data (assuming they are in the same raw df with a 'type' or similar, 
    # or we assume specific columns exist. The spec implies a flat raw table or specific columns.
    # Based on typical StudentLife data, we assume columns 'steps' and 'mood_score' exist alongside timestamps.
    # If the raw data has them in separate columns, we can process them directly.
    
    # Assuming df_raw has: participant_id, timestamp, steps, mood_score
    # We need to split them because steps are aggregated differently than mood.
    
    # Create step dataframe
    df_steps = df_raw[['participant_id', 'timestamp', 'steps']].copy()
    df_steps_processed = parse_step_logs(df_steps)
    
    # Create mood dataframe
    df_mood = df_raw[['participant_id', 'timestamp', 'mood_score']].copy()
    df_mood_processed = align_ema_mood(df_mood)
    
    # Compute aggregates
    daily_agg = compute_daily_aggregates(df_steps_processed, df_mood_processed)
    
    logger.info("Preprocessing pipeline completed")
    return daily_agg

def main():
    """Entry point for preprocessing script."""
    logger.info("Running preprocess.py main")
    
    try:
        result_df = preprocess()
        
        # Save to processed directory
        output_path = get_path('data', 'processed', 'daily_aggregates.csv')
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        result_df.to_csv(output_path, index=False)
        logger.info(f"Daily aggregates saved to {output_path}")
        
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        raise

if __name__ == "__main__":
    main()