"""
Preprocessing pipeline for StudentLife data.
Loads raw data, parses step logs, aligns EMA timestamps, and computes daily aggregates.
"""
import os
import sys
import logging
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import pyarrow.parquet as pq

# Import config for paths
# Using relative import structure expected in the project
try:
    from config import get_path, set_random_seed, DAILY_AGGREGATES_SCHEMA_PATH, PREPROCESS_STATS_PATH, BRONZE_PARQUET_PATH, DATA_PROCESSED_DIR
except ImportError:
    # Fallback for direct execution if package structure isn't set up yet
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from config import get_path, set_random_seed, DAILY_AGGREGATES_SCHEMA_PATH, PREPROCESS_STATS_PATH, BRONZE_PARQUET_PATH, DATA_PROCESSED_DIR

logger = logging.getLogger(__name__)

def load_bronze_data():
    """
    Load the raw bronze parquet file.
    """
    path = get_path('data', 'raw', 'bronze.parquet')
    if not os.path.exists(path):
        # Fallback to CSV if parquet doesn't exist yet (for robustness during initial runs)
        csv_path = get_path('data', 'raw', 'bronze.csv')
        if os.path.exists(csv_path):
            logger.warning(f"Parquet not found at {path}, trying CSV at {csv_path}")
            return pd.read_csv(csv_path)
        raise FileNotFoundError(f"Raw data file not found at {path}. Run ingest.py first.")
    
    logger.info(f"Loading bronze data from {path}")
    df = pd.read_parquet(path)
    return df

def parse_step_logs(df_raw):
    """
    Parse raw step logs into daily totals per participant.
    
    Args:
        df_raw (pd.DataFrame): DataFrame containing raw step logs.
            Expected columns: 'participant_id', 'timestamp', 'step_count' (or similar).
            
    Returns:
        pd.DataFrame: Aggregated step counts per participant per day.
    """
    logger.info("Parsing step logs...")
    
    # Ensure timestamp is datetime
    if 'timestamp' in df_raw.columns:
        df_raw['timestamp'] = pd.to_datetime(df_raw['timestamp'], errors='coerce')
    elif 'time' in df_raw.columns:
        df_raw['timestamp'] = pd.to_datetime(df_raw['time'], errors='coerce')
    else:
        # Try to find a column with 'date' or 'time' in name
        date_cols = [c for c in df_raw.columns if 'date' in c.lower() or 'time' in c.lower()]
        if date_cols:
            df_raw['timestamp'] = pd.to_datetime(df_raw[date_cols[0]], errors='coerce')
        else:
            raise ValueError("Could not identify timestamp column in step logs.")
    
    # Drop rows with invalid timestamps
    df_raw = df_raw.dropna(subset=['timestamp'])
    
    # Extract date
    df_raw['date'] = df_raw['timestamp'].dt.date
    
    # Identify step count column
    step_cols = [c for c in df_raw.columns if 'step' in c.lower() and 'count' in c.lower()]
    if not step_cols:
        step_cols = [c for c in df_raw.columns if 'step' in c.lower()]
    
    if not step_cols:
        raise ValueError("Could not identify step count column in step logs.")
    
    step_col = step_cols[0]
    
    # Ensure step count is numeric
    df_raw[step_col] = pd.to_numeric(df_raw[step_col], errors='coerce').fillna(0)
    
    # Group by participant and date
    # Assuming 'participant_id' is the column name
    if 'participant_id' not in df_raw.columns:
        # Try common alternatives
        pid_cols = [c for c in df_raw.columns if 'participant' in c.lower() or 'pid' in c.lower()]
        if pid_cols:
            df_raw['participant_id'] = df_raw[pid_cols[0]]
        else:
            raise ValueError("Could not identify participant_id column.")
    
    daily_steps = df_raw.groupby(['participant_id', 'date'])[step_col].sum().reset_index()
    daily_steps.rename(columns={step_col: 'total_steps'}, inplace=True)
    
    logger.info(f"Parsed step logs: {len(daily_steps)} participant-days")
    return daily_steps

def align_ema_mood(df_raw):
    """
    Align EMA mood timestamps and extract daily mood metrics.
    
    Args:
        df_raw (pd.DataFrame): Raw DataFrame containing mood/EMA data.
            
    Returns:
        pd.DataFrame: Daily mood aggregates (mean, std, count) per participant.
    """
    logger.info("Aligning EMA mood timestamps...")
    
    # Identify mood column
    mood_cols = [c for c in df_raw.columns if 'mood' in c.lower()]
    if not mood_cols:
        raise ValueError("Could not identify mood column.")
    mood_col = mood_cols[0]
    
    # Ensure mood is numeric
    df_raw[mood_col] = pd.to_numeric(df_raw[mood_col], errors='coerce')
    
    # Identify timestamp column
    ts_cols = [c for c in df_raw.columns if 'timestamp' in c.lower() or 'time' in c.lower()]
    if not ts_cols:
        raise ValueError("Could not identify timestamp column for EMA.")
    ts_col = ts_cols[0]
    
    df_raw[ts_col] = pd.to_datetime(df_raw[ts_col], errors='coerce')
    df_raw = df_raw.dropna(subset=[ts_col, mood_col])
    
    df_raw['date'] = df_raw[ts_col].dt.date
    
    if 'participant_id' not in df_raw.columns:
        pid_cols = [c for c in df_raw.columns if 'participant' in c.lower() or 'pid' in c.lower()]
        if pid_cols:
            df_raw['participant_id'] = df_raw[pid_cols[0]]
        else:
            raise ValueError("Could not identify participant_id column.")
    
    # Aggregate by participant and date
    mood_agg = df_raw.groupby(['participant_id', 'date'])[mood_col].agg(
        mean_mood='mean',
        mood_std='std',
        n_mood_ratings='count'
    ).reset_index()
    
    # Handle days with single rating (std is NaN) -> set to 0.0 as per spec T014 logic
    # But T014 says filter out < 2 ratings FIRST. So we keep NaN here and filter in compute_daily_aggregates
    # Actually, T014 says: "Filter out days with an insufficient number of valid mood ratings FIRST".
    # So we should not fill NaN here yet, we filter in the next step.
    
    logger.info(f"Aligned EMA mood: {len(mood_agg)} participant-days")
    return mood_agg

def derive_covariates(df_raw, daily_steps_df, daily_mood_df):
    """
    Derive sleep duration and baseline affect if missing.
    
    Args:
        df_raw: Raw data
        daily_steps_df: Daily steps dataframe
        daily_mood_df: Daily mood dataframe
        
    Returns:
        pd.DataFrame: Combined dataframe with derived covariates.
    """
    logger.info("Deriving covariates...")
    # Placeholder for actual derivation logic based on spec
    # This function is a stub to satisfy the structure, logic implemented in T012
    # For T011, we just ensure the function exists and signature is correct.
    # We assume T012 will fill in the logic.
    return daily_steps_df.merge(daily_mood_df, on=['participant_id', 'date'], how='outer')

def compute_daily_aggregates(daily_steps_df, daily_mood_df, df_raw=None):
    """
    Compute final daily aggregates.
    
    1. Filter out days with < 2 mood ratings.
    2. Compute mean_mood, mood_std (raw).
    3. Handle 0 variability (all identical) -> 0.0.
    4. Log excluded days.
    5. Ensure total_steps is 0 for days with zero steps.
    
    Args:
        daily_steps_df (pd.DataFrame): Daily steps.
        daily_mood_df (pd.DataFrame): Daily mood aggregates.
        df_raw: Raw data (optional, for covariates).
        
    Returns:
        pd.DataFrame: Final daily aggregates.
    """
    logger.info("Computing daily aggregates...")
    
    # Merge steps and mood
    df = daily_steps_df.merge(daily_mood_df, on=['participant_id', 'date'], how='outer')
    
    # Fill missing steps with 0
    df['total_steps'] = df['total_steps'].fillna(0).astype(int)
    
    # Filter out days with < 2 mood ratings FIRST
    # n_mood_ratings might be NaN if no mood data, treat as 0
    df['n_mood_ratings'] = df['n_mood_ratings'].fillna(0).astype(int)
    
    excluded_count = len(df[df['n_mood_ratings'] < 2])
    if excluded_count > 0:
        logger.warning(f"Excluding {excluded_count} days with < 2 mood ratings.")
        df = df[df['n_mood_ratings'] >= 2]
    
    # Write exclusion stats
    stats = {
        "excluded_days_count": int(excluded_count),
        "reason": "n_mood_ratings < 2"
    }
    stats_path = get_path('data', 'processed', 'preprocess_stats.json')
    os.makedirs(os.path.dirname(stats_path), exist_ok=True)
    with open(stats_path, 'w') as f:
        import json
        json.dump(stats, f, indent=2)
    
    # Handle mood_std
    # If n_mood_ratings >= 2, std should be calculable, but if all values same, std is 0.0
    # Pandas std returns NaN for n=1, but we filtered n<2, so n>=2.
    # If all values are identical, std is 0.0.
    # Ensure mood_std is not NaN (shouldn't be if n>=2, but just in case)
    df['mood_std'] = df['mood_std'].fillna(0.0)
    
    # Ensure mean_mood is present
    df['mean_mood'] = df['mean_mood'].fillna(0.0)
    
    # Derive day_of_week
    # We need to reconstruct date as datetime to get day_of_week
    df['date'] = pd.to_datetime(df['date'])
    df['day_of_week'] = df['date'].dt.dayofweek
    
    # Select final columns
    final_cols = ['participant_id', 'date', 'total_steps', 'mean_mood', 'mood_std', 'n_mood_ratings', 'day_of_week']
    # Add optional covariates if they exist
    optional_cols = ['sleep_duration', 'baseline_affect']
    for col in optional_cols:
        if col in df.columns:
            final_cols.append(col)
            df[col] = df[col].fillna(None) # Keep as nullable
    
    df_final = df[final_cols]
    
    # Assert no NaN/Inf in mood_std before writing (T015 requirement)
    if df_final['mood_std'].isna().any():
        raise ValueError("NaN found in mood_std column after processing.")
    if np.isinf(df_final['mood_std']).any():
        raise ValueError("Inf found in mood_std column after processing.")
        
    logger.info(f"Computed daily aggregates: {len(df_final)} rows")
    return df_final

def preprocess():
    """
    Main preprocessing pipeline.
    """
    logger.info("Starting preprocessing pipeline")
    set_random_seed()
    
    # Load raw data
    df_raw = load_bronze_data()
    
    # Parse step logs
    daily_steps = parse_step_logs(df_raw)
    
    # Align EMA mood
    daily_mood = align_ema_mood(df_raw)
    
    # Derive covariates (T012 logic placeholder)
    df_combined = derive_covariates(df_raw, daily_steps, daily_mood)
    
    # Compute aggregates
    df_final = compute_daily_aggregates(daily_steps, daily_mood, df_raw)
    
    return df_final

def main():
    """Entry point for preprocessing script."""
    logging.basicConfig(level=logging.INFO)
    try:
        result_df = preprocess()
        output_path = get_path('data', 'processed', 'daily_aggregates.csv')
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        result_df.to_csv(output_path, index=False)
        logger.info(f"Successfully wrote daily aggregates to {output_path}")
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        raise

if __name__ == "__main__":
    main()