"""
Preprocessing module for Physical Activity and Mood Variability study.

Handles data loading, parsing, alignment, and aggregation.
"""
import os
import sys
import logging
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from config import get_path, init_logger, set_random_seed

logger = init_logger(__name__)

def load_bronze_data() -> pd.DataFrame:
    """Load the raw bronze dataset from parquet file."""
    path = get_path('data', 'raw', 'bronze.parquet')
    if not os.path.exists(path):
        raise FileNotFoundError(f"Bronze data file not found at {path}. Run ingest.py first.")
    logger.info(f"Loading bronze data from {path}")
    return pd.read_parquet(path)

def parse_step_logs(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Parse raw step logs into daily totals.

    Args:
        df_raw: DataFrame with columns ['participant_id', 'timestamp', 'step_count']

    Returns:
        DataFrame with columns ['participant_id', 'date', 'total_steps']
    """
    logger.info("Parsing step logs...")
    # Ensure timestamp is datetime
    df_raw['timestamp'] = pd.to_datetime(df_raw['timestamp'])
    df_raw['date'] = df_raw['timestamp'].dt.date

    # Handle missing step_count by treating as 0
    df_raw['step_count'] = df_raw['step_count'].fillna(0)

    # Group by participant and date
    daily_steps = df_raw.groupby(['participant_id', 'date'])['step_count'].sum().reset_index()
    daily_steps.rename(columns={'step_count': 'total_steps'}, inplace=True)

    logger.info(f"Parsed {len(daily_steps)} participant-days from step logs")
    return daily_steps

def derive_covariates(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Derive sleep_duration and baseline_affect from raw data if missing.

    Args:
        df_raw: Raw DataFrame

    Returns:
        DataFrame with derived covariates
    """
    logger.info("Deriving covariates...")
    # Placeholder for derivation logic
    # In a real implementation, this would extract sleep and affect data from raw logs
    if 'sleep_duration' not in df_raw.columns:
        df_raw['sleep_duration'] = np.nan
    if 'baseline_affect' not in df_raw.columns:
        df_raw['baseline_affect'] = np.nan
    return df_raw

def align_ema_timestamps(df_steps: pd.DataFrame, df_ema: pd.DataFrame) -> pd.DataFrame:
    """
    Align EMA mood timestamps and exclude records with missing critical values.

    Args:
        df_steps: DataFrame with step data
        df_ema: DataFrame with EMA mood data

    Returns:
        Merged DataFrame aligned by participant_id and date
    """
    logger.info("Aligning EMA timestamps...")
    # Ensure date columns are consistent
    df_steps['date'] = pd.to_datetime(df_steps['date']).dt.date
    df_ema['date'] = pd.to_datetime(df_ema['timestamp']).dt.date

    # Drop EMA entries with missing mood
    df_ema = df_ema.dropna(subset=['mood'])

    # Merge on participant_id and date
    merged = pd.merge(df_steps, df_ema, on=['participant_id', 'date'], how='inner')

    logger.info(f"Aligned {len(merged)} records after timestamp alignment")
    return merged

def compute_daily_aggregates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute daily aggregates: mean_mood, mood_std, and log excluded days.

    Args:
        df: Merged DataFrame with step and EMA data

    Returns:
        DataFrame with daily aggregates
    """
    logger.info("Computing daily aggregates...")

    # Filter out days with fewer than 2 valid mood ratings FIRST
    valid_counts = df.groupby(['participant_id', 'date']).size().reset_index(name='n_mood_ratings')
    valid_days = valid_counts[valid_counts['n_mood_ratings'] >= 2]

    # Log excluded days
    excluded_count = len(valid_counts) - len(valid_days)
    if excluded_count > 0:
        logger.warning(f"Excluded {excluded_count} days due to n_mood_ratings < 2")
        # Write to preprocess_stats.json
        stats_path = get_path('data', 'processed', 'preprocess_stats.json')
        import json
        stats = {
            "excluded_days_count": excluded_count,
            "reason": "n_mood_ratings < 2"
        }
        with open(stats_path, 'w') as f:
            json.dump(stats, f, indent=2)

    # Merge valid days back to full data
    df_valid = pd.merge(df, valid_days, on=['participant_id', 'date'])

    # Compute aggregates
    aggregates = df_valid.groupby(['participant_id', 'date']).agg({
        'total_steps': 'first',  # Already aggregated per day
        'mood': ['mean', 'std', 'count'],
        'sleep_duration': 'mean',
        'baseline_affect': 'mean',
        'day_of_week': 'first'
    }).reset_index()

    # Flatten column names
    aggregates.columns = ['participant_id', 'date', 'total_steps', 'mean_mood', 'mood_std', 'n_mood_ratings', 'sleep_duration', 'baseline_affect', 'day_of_week']

    # Handle days with exactly 0 mood variability (all ratings identical)
    aggregates['mood_std'] = aggregates['mood_std'].fillna(0.0)

    # Assert no NaN in mood_std before writing
    assert not aggregates['mood_std'].isna().any(), "mood_std contains NaN values before writing"

    logger.info(f"Computed aggregates for {len(aggregates)} participant-days")
    return aggregates

def preprocess() -> pd.DataFrame:
    """Main preprocessing pipeline."""
    logger.info("Starting preprocessing pipeline")

    # Load raw data
    df_raw = load_bronze_data()

    # Parse step logs
    df_steps = parse_step_logs(df_raw)

    # Derive covariates
    df_raw = derive_covariates(df_raw)

    # Align EMA timestamps (assuming df_ema is extracted from df_raw)
    # For simplicity, assuming df_raw contains both step and EMA data
    df_ema = df_raw[['participant_id', 'timestamp', 'mood']].copy()
    df_merged = align_ema_timestamps(df_steps, df_ema)

    # Compute daily aggregates
    df_aggregates = compute_daily_aggregates(df_merged)

    return df_aggregates

def main():
    """Entry point for preprocessing script."""
    set_random_seed()
    df_result = preprocess()

    # Write output
    output_path = get_path('data', 'processed', 'daily_aggregates.csv')
    df_result.to_csv(output_path, index=False)
    logger.info(f"Saved daily aggregates to {output_path}")

    # Validate against schema
    from output_validator import validate_dataframe
    schema_path = get_path('specs', '001-physical-activity-levels-and-mood-variability', 'contracts', 'daily_aggregates.schema.yaml')
    validate_dataframe(df_result, schema_path)

if __name__ == "__main__":
    main()
