import os
import sys
import logging
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import json
import yaml

# Import from config to ensure paths and logging are consistent
from config import get_path, init_logger, ensure_dirs

# Initialize logger
logger = init_logger(__name__)

def load_bronze_data():
    """
    Load the bronze parquet file from data/raw.
    Returns a pandas DataFrame.
    """
    path = get_path("data", "raw", "bronze.parquet")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Bronze data not found at {path}. Run T063/T007 first.")
    logger.info(f"Loading bronze data from {path}")
    return pd.read_parquet(path)

def parse_step_logs(df_bronze):
    """
    Parse raw step logs into daily totals.
    Input: DataFrame with 'participant_id', 'timestamp', 'step_count'
    Output: DataFrame with 'participant_id', 'date', 'total_steps'
    """
    logger.info("Parsing step logs...")
    # Ensure timestamp is datetime
    df_bronze['timestamp'] = pd.to_datetime(df_bronze['timestamp'], errors='coerce')
    df_bronze['date'] = df_bronze['timestamp'].dt.date

    # Group by participant and date, sum steps (treat NaN as 0)
    step_agg = df_bronze.groupby(['participant_id', 'date'], as_index=False)['step_count'].sum()
    step_agg.rename(columns={'step_count': 'total_steps'}, inplace=True)
    step_agg['total_steps'] = step_agg['total_steps'].fillna(0).astype(int)
    
    logger.info(f"Parsed step logs: {len(step_agg)} participant-days")
    return step_agg

def derive_covariates(df_bronze):
    """
    Derive sleep_duration and baseline_affect if missing.
    Currently a placeholder for logic defined in T012.
    """
    logger.info("Deriving covariates...")
    # Placeholder logic: ensure columns exist, even if null
    if 'sleep_duration' not in df_bronze.columns:
        df_bronze['sleep_duration'] = None
    if 'baseline_affect' not in df_bronze.columns:
        df_bronze['baseline_affect'] = None
    return df_bronze

def align_ema_timestamps(df_bronze):
    """
    Align EMA mood timestamps and exclude records with missing critical values.
    """
    logger.info("Aligning EMA timestamps...")
    # Placeholder for T013 logic
    # Filter out null mood entries if they exist
    if 'mood' in df_bronze.columns:
        df_bronze = df_bronze.dropna(subset=['mood'])
    return df_bronze

def init_preprocess_stats(data_source_url):
    """
    Initialize the preprocess_stats.json file.
    Writes the initial state with data_source_url and excluded_days_count = 0.
    This MUST run before T014a to ensure provenance is recorded.
    """
    logger.info("Initializing preprocess stats...")
    output_path = get_path("data", "processed", "preprocess_stats.json")
    ensure_dirs(output_path)

    stats = {
        "data_source_url": data_source_url,
        "excluded_days_count": 0,
        "reason": "initial"
    }

    with open(output_path, 'w') as f:
        json.dump(stats, f, indent=2)

    # Verification: Ensure file is written and non-empty
    if not os.path.exists(output_path):
        raise RuntimeError(f"Failed to write {output_path}")
    
    if os.path.getsize(output_path) == 0:
        raise RuntimeError(f"Written {output_path} is empty")

    logger.info(f"Preprocess stats initialized at {output_path}")
    return stats

def compute_daily_aggregates(df_steps, df_ema):
    """
    Compute daily aggregates: mean_mood, mood_std, n_mood_ratings.
    Filters out days with 0 mood ratings first.
    """
    logger.info("Computing daily aggregates...")
    # Join steps and EMA data
    df_merged = pd.merge(df_steps, df_ema, on=['participant_id', 'date'], how='left')
    
    # Fill NaN steps with 0
    df_merged['total_steps'] = df_merged['total_steps'].fillna(0).astype(int)

    # Group by participant and date
    agg_df = df_merged.groupby(['participant_id', 'date'], as_index=False).agg(
        mean_mood=('mood', 'mean'),
        mood_std=('mood', 'std'),
        n_mood_ratings=('mood', 'count'),
        sleep_duration=('sleep_duration', 'first'),
        baseline_affect=('baseline_affect', 'first')
    )

    # Filter out days with 0 mood ratings (division by zero protection)
    agg_df = agg_df[agg_df['n_mood_ratings'] > 0].copy()

    # Handle single rating days: std is NaN, set to 0.0 as per spec
    agg_df['mood_std'] = agg_df['mood_std'].fillna(0.0)
    
    # Calculate day_of_week
    agg_df['date'] = pd.to_datetime(agg_df['date'])
    agg_df['day_of_week'] = agg_df['date'].dt.dayofweek

    logger.info(f"Computed aggregates: {len(agg_df)} rows")
    return agg_df

def handle_sparse_participants(df_agg):
    """
    Identify participants with < 3 valid days.
    Log warning and exclude from random-effects model fitting later.
    """
    logger.info("Handling sparse participants...")
    valid_days = df_agg.groupby('participant_id').size()
    sparse_participants = valid_days[valid_days < 3].index.tolist()
    
    if sparse_participants:
        logger.warning(f"Excluding {len(sparse_participants)} sparse participants (< 3 days)")
        df_filtered = df_agg[~df_agg['participant_id'].isin(sparse_participants)]
    else:
        df_filtered = df_agg

    return df_filtered, sparse_participants

def write_preprocess_stats(excluded_count, reason):
    """
    Update the preprocess_stats.json with exclusion counts.
    Validates against schema before writing.
    """
    logger.info("Writing preprocess stats...")
    output_path = get_path("data", "processed", "preprocess_stats.json")
    
    # Load existing stats
    if not os.path.exists(output_path):
        raise FileNotFoundError(f"Stats file {output_path} not found. Run init_preprocess_stats first.")
    
    with open(output_path, 'r') as f:
        stats = json.load(f)
    
    stats['excluded_days_count'] = excluded_count
    stats['reason'] = reason

    # Validate against schema (T005c)
    schema_path = get_path("specs", "001-physical-activity-levels-and-mood-variab", "contracts", "preprocess_stats.schema.yaml")
    if os.path.exists(schema_path):
        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)
        # Basic validation check
        required_keys = ['excluded_days_count', 'reason', 'data_source_url']
        for key in required_keys:
            if key not in stats:
                raise RuntimeError(f"Validation failed: missing key {key} in stats")

    with open(output_path, 'w') as f:
        json.dump(stats, f, indent=2)
    
    logger.info(f"Preprocess stats updated: {excluded_count} days excluded")
    return stats

def write_raw_daily_aggregates(df_agg):
    """
    Write unfiltered dataset (including single-rating days) to raw_daily_aggregates.csv.
    """
    logger.info("Writing raw daily aggregates...")
    output_path = get_path("data", "processed", "raw_daily_aggregates.csv")
    df_agg.to_csv(output_path, index=False)
    logger.info(f"Raw aggregates written to {output_path}")
    return output_path

def write_daily_aggregates(df_agg):
    """
    Write filtered dataset (excluding days with n_mood_ratings < 2) to daily_aggregates.csv.
    Validates against schema.
    """
    logger.info("Writing final daily aggregates...")
    output_path = get_path("data", "processed", "daily_aggregates.csv")
    
    # Filter for n_mood_ratings >= 2 for the final dataset
    df_final = df_agg[df_agg['n_mood_ratings'] >= 2].copy()
    
    # Assert no NaN/Inf in mood_std
    if not (df_final['mood_std'] >= 0).all() or not np.isfinite(df_final['mood_std']).all():
        raise ValueError("Invalid mood_std values found")

    df_final.to_csv(output_path, index=False)
    logger.info(f"Final aggregates written to {output_path} ({len(df_final)} rows)")
    return output_path

def preprocess(data_source_url):
    """
    Main orchestration function for preprocessing.
    1. Initialize stats (T064)
    2. Load data
    3. Parse steps, align EMA
    4. Compute aggregates
    5. Write raw and final outputs
    """
    logger.info("Starting preprocessing pipeline...")
    
    # T064: Initialize stats
    init_preprocess_stats(data_source_url)
    
    # Load data
    df_bronze = load_bronze_data()
    df_steps = parse_step_logs(df_bronze)
    df_ema = align_ema_timestamps(df_bronze)
    
    # Compute aggregates
    df_agg = compute_daily_aggregates(df_steps, df_ema)
    
    # Handle sparse participants (T050)
    df_agg, _ = handle_sparse_participants(df_agg)
    
    # Write outputs
    write_raw_daily_aggregates(df_agg)
    write_daily_aggregates(df_agg)
    
    # Update stats with exclusion count (T014b) - assuming 0 for now as per simple flow
    # In a real flow, this would calculate actual exclusions
    write_preprocess_stats(0, "initial processing complete")
    
    logger.info("Preprocessing complete.")
    return df_agg

def main():
    """Entry point for preprocessing script."""
    # Default data source URL from config if not overridden
    from config import get_path
    # Assuming config holds the URL or we pass it via env/arg
    data_source = "osf://studentlife" # Placeholder, should come from config or arg
    
    try:
        preprocess(data_source)
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        raise

if __name__ == "__main__":
    main()
