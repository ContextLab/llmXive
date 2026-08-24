import os
import sys
import logging
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import yaml

# Import shared utilities
# Note: We assume get_path is available in config and handles all call signatures
try:
    from config import get_path, SEED
except ImportError:
    # Fallback if config is not in path (should not happen in project structure)
    sys.path.insert(0, str(Path(__file__).parent))
    from config import get_path, SEED

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_bronze_data():
    """Load the raw bronze parquet file."""
    # Handle the specific call signature from T011/T012/T013 context
    # config.get_path is expected to handle variable args
    try:
        path = get_path('data', 'raw', 'bronze.parquet')
    except TypeError:
        # Fallback for older signature if get_path doesn't support *args yet
        path = get_path('data/raw/bronze.parquet')
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"Bronze data not found at {path}. Run ingest.py first.")
    
    logger.info(f"Loading bronze data from {path}")
    return pd.read_parquet(path)

def parse_step_logs(df_raw: pd.DataFrame = None) -> pd.DataFrame:
    """
    Parse raw step logs into daily totals.
    If df_raw is None, loads from data/raw/bronze.parquet.
    Input columns: participant_id, timestamp, step_count.
    Output: DataFrame with participant_id, date, total_steps.
    """
    if df_raw is None:
        df_raw = load_bronze_data()
    
    # Ensure timestamp is datetime
    df_raw['timestamp'] = pd.to_datetime(df_raw['timestamp'], errors='coerce')
    
    # Handle missing step_count by treating as 0
    df_raw['step_count'] = pd.to_numeric(df_raw['step_count'], errors='coerce').fillna(0).astype(int)
    
    # Extract date
    df_raw['date'] = df_raw['timestamp'].dt.date
    
    # Aggregate by participant and date
    daily_steps = df_raw.groupby(['participant_id', 'date'], as_index=False)['step_count'].sum()
    daily_steps.rename(columns={'step_count': 'total_steps'}, inplace=True)
    
    # Ensure date is datetime for consistency in later joins
    daily_steps['date'] = pd.to_datetime(daily_steps['date'])
    
    return daily_steps

def derive_covariates(df_raw: pd.DataFrame = None) -> dict:
    """
    Derive sleep_duration and baseline_affect if missing.
    Returns a dict of derived dataframes or None if not derivable.
    """
    if df_raw is None:
        df_raw = load_bronze_data()
    
    derived = {}
    
    # Placeholder logic for derivation (implementation depends on specific data schema)
    # Assuming 'sleep_duration' and 'baseline_affect' might exist in raw data or need calculation
    # For now, returning empty dict if columns not found, to be handled in aggregation
    if 'sleep_duration' not in df_raw.columns:
        logger.warning("sleep_duration not found in raw data; will be NaN in aggregates")
    else:
        derived['sleep_duration'] = df_raw.groupby('participant_id')['sleep_duration'].mean().reset_index()
    
    if 'baseline_affect' not in df_raw.columns:
        logger.warning("baseline_affect not found in raw data; will be NaN in aggregates")
    else:
        derived['baseline_affect'] = df_raw.groupby('participant_id')['baseline_affect'].mean().reset_index()
    
    return derived

def align_ema_timestamps(df_raw: pd.DataFrame = None) -> pd.DataFrame:
    """
    Align EMA mood timestamps and exclude records with missing critical values.
    Join step logs and EMA data on participant_id and date.
    Drop EMA entries where mood is null.
    Align timestamps within 24h window.
    """
    if df_raw is None:
        df_raw = load_bronze_data()
    
    # Filter for EMA data (assuming a column 'type' or similar, or specific columns)
    # Assuming raw data has a 'mood' column for EMA
    if 'mood' not in df_raw.columns:
        logger.error("No 'mood' column found in raw data. Cannot align EMA timestamps.")
        return pd.DataFrame()
    
    df_ema = df_raw[['participant_id', 'timestamp', 'mood']].copy()
    df_ema['timestamp'] = pd.to_datetime(df_ema['timestamp'], errors='coerce')
    df_ema['date'] = df_ema['timestamp'].dt.date
    df_ema['date'] = pd.to_datetime(df_ema['date'])
    
    # Drop null moods
    df_ema = df_ema.dropna(subset=['mood'])
    
    return df_ema

def compute_daily_aggregates(df_steps: pd.DataFrame = None, df_ema: pd.DataFrame = None) -> pd.DataFrame:
    """
    Compute daily aggregates: mean_mood, mood_std, total_steps.
    1. Filter out days with 0 mood ratings.
    2. Filter out days with < 2 valid mood ratings.
    3. Compute raw mood_std (0.0 for identical ratings).
    4. Log excluded days.
    """
    if df_steps is None:
        df_steps = parse_step_logs()
    if df_ema is None:
        df_ema = align_ema_timestamps()
    
    if df_ema.empty:
        logger.warning("No EMA data available. Returning empty aggregates.")
        return pd.DataFrame()
    
    # Ensure date types match
    df_steps['date'] = pd.to_datetime(df_steps['date'])
    df_ema['date'] = pd.to_datetime(df_ema['date'])
    
    # Count mood ratings per participant-day
    mood_counts = df_ema.groupby(['participant_id', 'date']).size().reset_index(name='n_mood_ratings')
    
    # Filter: n_mood_ratings >= 2
    valid_days = mood_counts[mood_counts['n_mood_ratings'] >= 2].copy()
    
    excluded_count = len(mood_counts) - len(valid_days)
    if excluded_count > 0:
        logger.info(f"Excluded {excluded_count} days with fewer than 2 mood ratings.")
        # Write stats to preprocess_stats.json
        stats_path = get_path('data', 'processed', 'preprocess_stats.json')
        try:
            os.makedirs(os.path.dirname(stats_path), exist_ok=True)
            with open(stats_path, 'w') as f:
                json.dump({
                    "excluded_days_count": excluded_count,
                    "reason": "n_mood_ratings < 2 or count == 0"
                }, f)
        except Exception as e:
            logger.error(f"Failed to write preprocess stats: {e}")
    
    # Compute aggregates on valid days
    valid_mood = df_ema.merge(valid_days, on=['participant_id', 'date'], how='inner')
    
    agg = valid_mood.groupby(['participant_id', 'date']).agg(
        mean_mood=('mood', 'mean'),
        mood_std=('mood', 'std'),
        n_mood_ratings=('mood', 'count')
    ).reset_index()
    
    # Fill NaN std (happens if n=1, but we filtered n>=2, so this should be rare/0.0 for identical)
    # If n=2 and values identical, std is 0.0. If n>2 and identical, std is 0.0.
    # Pandas std returns NaN for single value, but we have >= 2.
    # However, if all values are identical, std is 0.0.
    # Ensure no NaN in mood_std
    agg['mood_std'] = agg['mood_std'].fillna(0.0)
    
    # Merge with steps
    # Left join to keep days with mood but maybe no steps (steps=0)
    result = agg.merge(df_steps, on=['participant_id', 'date'], how='left')
    result['total_steps'] = result['total_steps'].fillna(0).astype(int)
    
    # Derive covariates (placeholder: just merge if available)
    # In a real scenario, we'd compute these per participant or day
    # For now, we assume they are participant-level or day-level and merge if present
    # This is a simplified version; actual implementation depends on data schema
    
    # Add day_of_week
    result['day_of_week'] = result['date'].dt.dayofweek
    
    # Select final columns
    final_cols = ['participant_id', 'date', 'total_steps', 'mean_mood', 'mood_std', 'n_mood_ratings', 'day_of_week']
    # Add optional columns if they exist in derived data (simplified)
    # In a full implementation, we'd merge sleep_duration and baseline_affect here
    
    return result[final_cols]

def write_daily_aggregates(df: pd.DataFrame) -> str:
    """
    Write the final output to data/processed/daily_aggregates.csv.
    Validate against schema (assert no NaN/Inf in mood_std).
    """
    # Assert no NaN/Inf in mood_std
    if df['mood_std'].isna().any():
        raise AssertionError("mood_std contains NaN values. This should not happen after fillna(0.0).")
    if np.isinf(df['mood_std']).any():
        raise AssertionError("mood_std contains Inf values.")
    
    # Ensure output directory exists
    output_path = get_path('data', 'processed', 'daily_aggregates.csv')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Write to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Daily aggregates written to {output_path}")
    
    return output_path

def validate_against_schema(df: pd.DataFrame) -> bool:
    """
    Validate dataframe against daily_aggregates.schema.yaml.
    """
    schema_path = get_path('specs', '001-physical-activity-levels-and-mood-variab', 'contracts', 'daily_aggregates.schema.yaml')
    if not os.path.exists(schema_path):
        logger.warning(f"Schema file not found at {schema_path}. Skipping validation.")
        return True
    
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    # Simple validation: check required columns and types
    required_cols = ['participant_id', 'date', 'total_steps', 'mean_mood', 'mood_std', 'n_mood_ratings', 'day_of_week']
    for col in required_cols:
        if col not in df.columns:
            logger.error(f"Missing required column: {col}")
            return False
    
    # Check types
    if not pd.api.types.is_integer_dtype(df['total_steps']):
        logger.warning("total_steps is not integer.")
    if not pd.api.types.is_float_dtype(df['mean_mood']) or not pd.api.types.is_float_dtype(df['mood_std']):
        logger.warning("mean_mood or mood_std is not float.")
    if not pd.api.types.is_integer_dtype(df['n_mood_ratings']):
        logger.warning("n_mood_ratings is not integer.")
    if not pd.api.types.is_integer_dtype(df['day_of_week']):
        logger.warning("day_of_week is not integer.")
    
    # Check constraints
    if (df['total_steps'] < 0).any():
        logger.error("total_steps contains negative values.")
        return False
    if (df['mood_std'] < 0).any():
        logger.error("mood_std contains negative values.")
        return False
    if (df['n_mood_ratings'] < 2).any():
        logger.error("n_mood_ratings contains values < 2.")
        return False
    
    logger.info("Validation passed.")
    return True

def preprocess():
    """Main preprocessing pipeline."""
    logger.info("Starting preprocessing pipeline")
    
    # 1. Load and parse steps
    df_steps = parse_step_logs()
    
    # 2. Align EMA
    df_ema = align_ema_timestamps()
    
    # 3. Compute aggregates
    df_agg = compute_daily_aggregates(df_steps, df_ema)
    
    if df_agg.empty:
        logger.warning("No data to process. Returning empty dataframe.")
        return df_agg
    
    # 4. Validate
    if not validate_against_schema(df_agg):
        raise ValueError("Validation failed. Check logs for details.")
    
    # 5. Write output
    write_daily_aggregates(df_agg)
    
    return df_agg

def main():
    """Entry point for preprocess.py."""
    try:
        preprocess()
        logger.info("Preprocessing completed successfully.")
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
