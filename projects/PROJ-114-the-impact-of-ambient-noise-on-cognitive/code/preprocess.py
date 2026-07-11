"""
Preprocessing module for the Ambient Noise and Cognitive Flexibility study.
Implements data cleaning, filtering, and normalization pipelines.
"""
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from .config import ROOT_DIR, MAD_OUTLIER_THRESHOLD

logger = logging.getLogger(__name__)

def filter_participants(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter participants based on data validity and task completion rates.

    Excludes logs where:
    - Valid logging hours < 80%
    - Task completion rate < 90%

    Args:
        df: DataFrame containing participant logs with columns:
            - 'participant_id'
            - 'valid_logging_hours_pct'
            - 'task_completion_rate'

    Returns:
        Filtered DataFrame containing only valid participants.
    """
    if df.empty:
        logger.warning("Input DataFrame is empty in filter_participants")
        return df

    # Apply filtering criteria
    mask = (
        (df['valid_logging_hours_pct'] >= 0.80) &
        (df['task_completion_rate'] >= 0.90)
    )

    filtered_df = df[mask].copy()
    excluded_count = len(df) - len(filtered_df)

    logger.info(
        f"Filtered participants: {excluded_count} excluded, "
        f"{len(filtered_df)} retained."
    )

    return filtered_df

def normalize_reaction_times(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize reaction times using log-transformation and MAD outlier removal.

    Per participant:
    1. Apply log-transformation (log1p) to reaction times to handle skewness.
    2. Calculate Median Absolute Deviation (MAD) of the log-transformed times.
    3. Remove outliers where absolute deviation > 3.5 * MAD.

    Args:
        df: DataFrame containing reaction time data with columns:
            - 'participant_id'
            - 'reaction_time' (in milliseconds or seconds)

    Returns:
        DataFrame with normalized reaction times and outliers removed.
    """
    if df.empty:
        logger.warning("Input DataFrame is empty in normalize_reaction_times")
        return df

    # Ensure we have a copy to avoid SettingWithCopyWarning
    result_df = df.copy()

    # Ensure reaction_time is numeric
    result_df['reaction_time'] = pd.to_numeric(
        result_df['reaction_time'], errors='coerce'
    )

    # Drop rows with invalid reaction times before processing
    valid_mask = result_df['reaction_time'].notna()
    result_df = result_df[valid_mask].copy()

    if result_df.empty:
        logger.warning("No valid reaction times found after coercion")
        return result_df

    # Apply log transformation (log1p handles zero values safely)
    result_df['reaction_time_log'] = np.log1p(result_df['reaction_time'])

    # Group by participant to calculate MAD per participant
    def remove_outliers(group):
        if len(group) < 3:
            # Not enough data points to calculate meaningful MAD
            logger.debug(
                f"Participant {group['participant_id'].iloc[0]} has "
                f"< 3 data points, skipping outlier removal."
            )
            return group

        log_times = group['reaction_time_log']
        median = log_times.median()
        mad = np.median(np.abs(log_times - median))

        if mad == 0:
            # All values are identical or very close; keep all
            logger.debug(
                f"Participant {group['participant_id'].iloc[0]} has MAD=0, "
                f"keeping all data points."
            )
            return group

        # Calculate absolute deviation from median
        abs_dev = np.abs(log_times - median)

        # Define threshold
        threshold = MAD_OUTLIER_THRESHOLD * mad

        # Keep rows within threshold
        mask = abs_dev <= threshold
        return group[mask]

    # Apply outlier removal per participant
    cleaned_df = result_df.groupby('participant_id', group_keys=False).apply(
        remove_outliers
    )

    # Reset index if necessary
    cleaned_df = cleaned_df.reset_index(drop=True)

    retained = len(result_df)
    removed = retained - len(cleaned_df)

    logger.info(
        f"Normalized reaction times: {removed} outliers removed, "
        f"{len(cleaned_df)} retained."
    )

    return cleaned_df

def aggregate_noise_logs(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate continuous decibel values into average and hourly variability.

    Calculates:
    - Average decibel level per participant/session
    - Standard deviation of decibel levels per participant/session

    Args:
        df: DataFrame containing noise logs with columns:
            - 'participant_id'
            - 'decibel_level'
            - 'timestamp' (optional, for time-based aggregation)

    Returns:
        DataFrame with aggregated noise metrics.
    """
    if df.empty:
        logger.warning("Input DataFrame is empty in aggregate_noise_logs")
        return df

    agg_df = df.groupby('participant_id').agg(
        avg_noise=('decibel_level', 'mean'),
        noise_std=('decibel_level', 'std')
    ).reset_index()

    # Fill NaN std for participants with single measurement
    agg_df['noise_std'] = agg_df['noise_std'].fillna(0.0)

    logger.info(
        f"Aggregated noise logs for {len(agg_df)} participants."
    )

    return agg_df

def create_noise_bins(df: pd.DataFrame) -> pd.DataFrame:
    """
    Categorize continuous average noise levels into bins (Low, Moderate, High).

    Thresholds (from config):
    - Low: < NOISE_THRESHOLD_LOW
    - Moderate: NOISE_THRESHOLD_LOW <= x < NOISE_THRESHOLD_HIGH
    - High: >= NOISE_THRESHOLD_HIGH

    Args:
        df: DataFrame containing 'avg_noise' column and 'noise_sensitivity_score'.

    Returns:
        DataFrame with added 'noise_level' categorical column.
    """
    from .config import NOISE_THRESHOLD_LOW, NOISE_THRESHOLD_HIGH

    if df.empty:
        logger.warning("Input DataFrame is empty in create_noise_bins")
        return df

    def categorize_noise(val):
        if pd.isna(val):
            return np.nan
        if val < NOISE_THRESHOLD_LOW:
            return 'Low'
        elif val < NOISE_THRESHOLD_HIGH:
            return 'Moderate'
        else:
            return 'High'

    df = df.copy()
    df['noise_level'] = df['avg_noise'].apply(categorize_noise)

    logger.info(f"Created noise bins: {df['noise_level'].value_counts().to_dict()}")

    return df

def run_full_preprocessing(
    raw_data_path: str,
    output_path: str
) -> pd.DataFrame:
    """
    Execute the full preprocessing pipeline:
    1. Load raw data
    2. Filter participants
    3. Normalize reaction times
    4. Aggregate noise logs
    5. Create noise bins
    6. Save output

    Args:
        raw_data_path: Path to the raw input CSV/Parquet file.
        output_path: Path to save the processed dataset.

    Returns:
        The final processed DataFrame.
    """
    raw_path = Path(raw_data_path)
    out_path = Path(output_path)

    logger.info(f"Starting preprocessing pipeline from {raw_path}")

    # Load data (handle both csv and parquet)
    if raw_path.suffix == '.csv':
        df = pd.read_csv(raw_path)
    else:
        df = pd.read_parquet(raw_path)

    # Step 1: Filter participants
    df = filter_participants(df)

    # Step 2: Normalize reaction times (requires reaction_time column)
    # Only run if the column exists
    if 'reaction_time' in df.columns:
        df = normalize_reaction_times(df)
    else:
        logger.warning("Column 'reaction_time' not found, skipping normalization.")

    # Step 3: Aggregate noise logs (requires decibel_level column)
    if 'decibel_level' in df.columns:
        # We need to merge aggregated noise back if it's a separate log file
        # Assuming for this pipeline that noise logs are merged or we aggregate here
        # If the input is a merged table, we group by participant_id
        noise_agg = aggregate_noise_logs(df)
        
        # Merge noise aggregates back to main df if they are separate
        # If the input df already has aggregated noise, this step might be redundant
        # but we assume the raw data has per-event logs.
        # For this implementation, we assume the input is already participant-level
        # or we need to merge. Let's assume the input `df` has the raw rows
        # and we need to merge the aggregated noise stats.
        
        # If 'avg_noise' already exists in df, skip aggregation
        if 'avg_noise' not in df.columns:
            # Merge noise stats
            df = df.merge(noise_agg, on='participant_id', how='left')
    else:
        logger.warning("Column 'decibel_level' not found, skipping noise aggregation.")

    # Step 4: Create noise bins
    if 'avg_noise' in df.columns:
        df = create_noise_bins(df)
    else:
        logger.warning("Column 'avg_noise' not found, skipping noise binning.")

    # Ensure output directory exists
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Save output
    if out_path.suffix == '.parquet':
        df.to_parquet(out_path, index=False)
    else:
        df.to_csv(out_path, index=False)

    logger.info(f"Preprocessing complete. Output saved to {out_path}")
    return df