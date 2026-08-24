"""
Preprocessing pipeline for StudentLife dataset.
Handles ingestion, parsing, alignment, and aggregation of daily data.
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import yaml
import json

from config import get_path, init_logger, SEED
from ingest import download_and_verify

# Initialize logger
logger = init_logger(__name__)

def load_bronze_data():
    """Load the bronze parquet file."""
    path = get_path("data", "raw", "bronze.parquet")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Bronze data not found at {path}. Run ingest.py first.")
    logger.info(f"Loading bronze data from {path}")
    return pd.read_parquet(path)

def parse_step_logs(df):
    """
    Parse raw step logs into daily totals.
    Input columns: participant_id, timestamp, step_count
    Output: DataFrame with participant_id, date, total_steps
    """
    logger.info("Parsing step logs...")
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['date'] = df['timestamp'].dt.date
    else:
        raise ValueError("Missing 'timestamp' column in step logs.")

    # Handle missing step_count by treating as 0
    df['step_count'] = df['step_count'].fillna(0).astype(int)

    # Group by participant and date
    step_agg = df.groupby(['participant_id', 'date'])['step_count'].sum().reset_index()
    step_agg.columns = ['participant_id', 'date', 'total_steps']
    logger.info(f"Parsed step logs: {len(step_agg)} daily records")
    return step_agg

def derive_covariates(df):
    """
    Derive sleep_duration and baseline_affect if missing.
    Uses config.MISSINGNESS_THRESHOLD to decide derivation.
    """
    logger.info("Deriving covariates...")
    # Placeholder logic for derivation based on spec assumptions
    # In a real scenario, this would calculate from raw EMA or sensor data
    # For now, we ensure columns exist if they are expected downstream
    if 'sleep_duration' not in df.columns:
        df['sleep_duration'] = np.nan
    if 'baseline_affect' not in df.columns:
        df['baseline_affect'] = np.nan
    return df

def align_ema_timestamps(df_steps, df_ema):
    """
    Align EMA mood timestamps and exclude records with missing critical values.
    Join step logs and EMA data on participant_id and date.
    Drop EMA entries where mood is null.
    Tolerance: 24h window (handled by date alignment).
    """
    logger.info("Aligning EMA timestamps...")
    if 'timestamp' in df_ema.columns:
        df_ema['date'] = pd.to_datetime(df_ema['timestamp']).dt.date
    else:
        raise ValueError("Missing 'timestamp' column in EMA data.")

    # Drop null mood entries
    df_ema = df_ema.dropna(subset=['mood'])

    # Merge on participant_id and date
    merged = pd.merge(
        df_steps,
        df_ema[['participant_id', 'date', 'mood']],
        on=['participant_id', 'date'],
        how='inner'
    )
    logger.info(f"Aligned {len(merged)} records after dropping nulls")
    return merged

def handle_sparse_participants(df, min_days=3):
    """
    Identify participants with < min_days valid days.
    Log warning and exclude them from random-effects model fitting.
    Returns filtered dataset and list of excluded IDs.
    """
    logger.info(f"Handling sparse participants (min_days={min_days})...")
    counts = df.groupby('participant_id').size()
    excluded_ids = counts[counts < min_days].index.tolist()
    if excluded_ids:
        logger.warning(f"Excluding {len(excluded_ids)} participants with < {min_days} days: {excluded_ids}")
    filtered = df[~df['participant_id'].isin(excluded_ids)]
    return filtered, excluded_ids

def write_preprocess_stats(excluded_count, reason):
    """Write preprocessing statistics to JSON."""
    stats = {
        "excluded_days_count": excluded_count,
        "reason": reason
    }
    path = get_path("data", "processed", "preprocess_stats.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(stats, f, indent=2)
    logger.info(f"Preprocess stats written to {path}")

def validate_against_schema(df, schema_path):
    """Validate DataFrame against a YAML schema."""
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    required_fields = schema.get('properties', {}).keys()
    for field in required_fields:
        if field not in df.columns:
            raise ValueError(f"Missing required column: {field}")
    
    # Type checks based on schema (simplified)
    if 'total_steps' in df.columns and df['total_steps'].dtype not in [np.int64, np.int32, float]:
        # Allow float if it represents integer values
        if not df['total_steps'].apply(lambda x: isinstance(x, (int, float)) and x >= 0).all():
            raise ValueError("total_steps must be non-negative integers.")
    
    return True

def compute_daily_aggregates(df):
    """
    Compute daily aggregates: mean_mood, mood_std, n_mood_ratings.
    1. Filter out days with 0 mood ratings.
    2. Filter out days with < 2 valid mood ratings.
    3. Compute raw mood_std (0.0 for identical ratings).
    4. Log excluded days count.
    """
    logger.info("Computing daily aggregates...")
    
    # Ensure date is datetime for grouping
    if not isinstance(df['date'].iloc[0], datetime):
        df['date'] = pd.to_datetime(df['date'])
    
    # Group by participant and date
    agg = df.groupby(['participant_id', 'date']).agg(
        total_steps=('total_steps', 'first'), # Assuming total_steps is constant per day in merged data
        mean_mood=('mood', 'mean'),
        mood_std=('mood', 'std'),
        n_mood_ratings=('mood', 'count')
    ).reset_index()

    # Handle days with 0 ratings (should be dropped by groupby if inner join, but explicit check)
    # Filter days with n_mood_ratings < 2
    excluded_count = len(agg[agg['n_mood_ratings'] < 2])
    valid_agg = agg[agg['n_mood_ratings'] >= 2].copy()

    # Write stats
    write_preprocess_stats(excluded_count, "n_mood_ratings < 2 or count == 0")

    # Fill NaN std with 0.0 (for days with 1 rating, though filtered, or identical ratings)
    valid_agg['mood_std'] = valid_agg['mood_std'].fillna(0.0)
    
    # Ensure types
    valid_agg['total_steps'] = valid_agg['total_steps'].fillna(0).astype(int)
    valid_agg['mean_mood'] = valid_agg['mean_mood'].astype(float)
    valid_agg['mood_std'] = valid_agg['mood_std'].astype(float)
    valid_agg['n_mood_ratings'] = valid_agg['n_mood_ratings'].astype(int)
    
    # Add derived columns if missing
    if 'sleep_duration' not in valid_agg.columns:
        valid_agg['sleep_duration'] = np.nan
    if 'baseline_affect' not in valid_agg.columns:
        valid_agg['baseline_affect'] = np.nan
    if 'day_of_week' not in valid_agg.columns:
        valid_agg['day_of_week'] = pd.to_datetime(valid_agg['date']).dt.dayofweek

    logger.info(f"Computed {len(valid_agg)} daily aggregates")
    return valid_agg

def write_daily_aggregates(df):
    """Write final output to CSV and validate against schema."""
    logger.info("Writing daily aggregates to CSV...")
    output_path = get_path("data", "processed", "daily_aggregates.csv")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Final validation: Assert no NaN/Inf in mood_std
    assert (df['mood_std'] >= 0).all(), "mood_std contains negative values"
    assert np.isfinite(df['mood_std']).all(), "mood_std contains NaN or Inf values"
    
    # Validate against schema
    schema_path = get_path("specs", "001-physical-activity-levels-and-mood-variab", "contracts", "daily_aggregates.schema.yaml")
    validate_against_schema(df, schema_path)

    df.to_csv(output_path, index=False)
    logger.info(f"Daily aggregates written to {output_path}")
    return output_path

def preprocess():
    """Main preprocessing pipeline."""
    logger.info("Starting preprocessing pipeline")
    try:
        # Load bronze data
        df_bronze = load_bronze_data()
        
        # Split into steps and EMA (assuming columns distinguish them or separate tables in parquet)
        # Assuming bronze.parquet has a 'source' or similar, or we split by columns
        # For this implementation, we assume the parquet has all raw data and we filter
        if 'step_count' in df_bronze.columns and 'mood' in df_bronze.columns:
            # Mixed data: separate by logic
            # This is a simplification; real data might have separate tables
            df_steps = df_bronze[df_bronze['step_count'].notna()].copy()
            df_ema = df_bronze[df_bronze['mood'].notna()].copy()
        else:
            # Assume separate tables or specific structure
            # Fallback: try to parse based on common column names
            raise ValueError("Could not automatically separate step logs and EMA data. Check schema.")

        # Parse steps
        df_steps_parsed = parse_step_logs(df_steps)
        
        # Align EMA
        df_aligned = align_ema_timestamps(df_steps_parsed, df_ema)
        
        # Derive covariates
        df_aligned = derive_covariates(df_aligned)
        
        # Compute aggregates
        df_agg = compute_daily_aggregates(df_aligned)
        
        # Handle sparse participants
        df_filtered, excluded = handle_sparse_participants(df_agg)
        
        # Write output
        write_daily_aggregates(df_filtered)
        
        logger.info("Preprocessing pipeline completed successfully")
        return df_filtered
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        raise

def main():
    """Entry point for preprocessing."""
    preprocess()

if __name__ == "__main__":
    main()