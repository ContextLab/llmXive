import pandas as pd
import numpy as np
from typing import List, Optional, Tuple, Dict
from pathlib import Path
import logging
from src.lib.utils import load_csv, save_csv, setup_logging

logger = logging.getLogger(__name__)

def exclude_multicollinear_features(df: pd.DataFrame, feature_cols: List[str]) -> pd.DataFrame:
    """
    Exclude specific features known to cause multicollinearity.
    Currently excludes 'gdd_cumulative' as per T021 requirement.
    """
    cols_to_drop = ['gdd_cumulative']
    existing_cols = [c for c in cols_to_drop if c in df.columns]
    if existing_cols:
        logger.info(f"Dropping multicollinear features: {existing_cols}")
        return df.drop(columns=existing_cols)
    return df

def interpolate_time_series(df: pd.DataFrame, date_col: str = 'date', value_cols: List[str] = None) -> Tuple[pd.DataFrame, int]:
    """
    Perform linear interpolation on time series data.
    - Interpolates if <= 1 consecutive 10-day gap.
    - Excludes rows if > 1 consecutive gap.
    - Returns the cleaned dataframe and count of excluded rows.
    """
    if value_cols is None:
        # Assume all numeric columns except the date and ID columns need interpolation
        value_cols = [c for c in df.columns if c != date_col and c not in ['site_id', 'phenology_date']]

    df = df.sort_values(by=[date_col])
    excluded_count = 0

    for col in value_cols:
        if col not in df.columns:
            continue
        
        # Identify gaps (NaN)
        is_na = df[col].isna()
        
        # Count consecutive NaNs
        # Create a group ID for consecutive NaNs
        is_not_na = ~is_na
        group_id = is_not_na.cumsum()
        
        # Filter to only NaN groups
        nan_groups = is_na.groupby(group_id).sum()
        
        # Identify groups with > 1 consecutive NaN
        bad_groups = nan_groups[nan_groups > 1].index
        
        if len(bad_groups) > 0:
            # Mark rows in bad groups for exclusion
            mask_bad = is_na & is_not_na.groupby(group_id).transform(lambda x: x.name in bad_groups)
            # Actually, we need to mark the specific rows that are part of a bad gap
            # Re-calculate: rows where the gap size > 1
            gap_size = is_na.groupby(group_id).transform('sum')
            rows_to_drop = is_na & (gap_size > 1)
            
            if rows_to_drop.any():
                logger.warning(f"Dropping {rows_to_drop.sum()} rows in {col} due to >1 consecutive gap.")
                df = df.drop(df.index[rows_to_drop])
                excluded_count += rows_to_drop.sum()
                is_na = df[col].isna()
                group_id = (~is_na).cumsum()
                gap_size = is_na.groupby(group_id).transform('sum')
        
        # Interpolate remaining NaNs (linear)
        if is_na.any():
            df[col] = df[col].interpolate(method='linear')

    return df.reset_index(drop=True), excluded_count

def filter_insufficient_data(df: pd.DataFrame, min_coverage: float = 0.8, obs_col: str = 'observations') -> pd.DataFrame:
    """
    Filter out sites with insufficient data coverage or zero observations in critical windows.
    """
    if obs_col not in df.columns:
        # If no specific obs column, count non-null rows per site
        obs_counts = df.groupby('site_id').apply(lambda x: x.notna().sum().mean())
    else:
        obs_counts = df.groupby('site_id')[obs_col].count()
    
    total_obs = len(df) // df['site_id'].nunique() if 'site_id' in df.columns else len(df)
    
    # Calculate coverage
    coverage = obs_counts / total_obs
    
    insufficient_sites = coverage[coverage < min_coverage].index.tolist()
    
    if insufficient_sites:
        logger.warning(f"Filtering out {len(insufficient_sites)} sites with < {min_coverage*100}% data coverage.")
        return df[~df['site_id'].isin(insufficient_sites)]
    
    return df

def mask_missing_phenology_labels(df: pd.DataFrame, phenology_col: str = 'phenology_date') -> pd.DataFrame:
    """
    Handle missing phenology labels by masking rows during training rather than imputation.
    
    This function does NOT drop rows or fill values. Instead, it creates a boolean
    mask column 'is_valid_label' indicating whether the phenology label is present.
    Downstream training logic (e.g., in train.py) should use this mask to exclude
    rows from loss calculation or training steps where the target is missing.
    
    Args:
        df: Input dataframe containing phenology data.
        phenology_col: Name of the column containing the target phenology date.
    
    Returns:
        DataFrame with an added 'is_valid_label' column (True if label exists, False otherwise).
    """
    if phenology_col not in df.columns:
        logger.warning(f"Column '{phenology_col}' not found in dataframe. Cannot mask missing labels.")
        df['is_valid_label'] = True  # Default to True if column missing, or False? 
        # If the column is missing entirely, we can't predict it. 
        # However, per task T016, we are handling *missing labels* in an existing column.
        # If the column doesn't exist, the whole dataset is invalid for this task.
        # Let's assume the column exists but has NaNs.
        raise ValueError(f"Required column '{phenology_col}' not found in dataframe.")
    
    df['is_valid_label'] = df[phenology_col].notna()
    
    missing_count = (~df['is_valid_label']).sum()
    total_count = len(df)
    
    if missing_count > 0:
        logger.info(f"Masked {missing_count} rows ({missing_count/total_count:.2%}) with missing phenology labels.")
    else:
        logger.info("No missing phenology labels found.")
    
    return df

def run_preprocessing(input_path: str, output_path: str, phenology_col: str = 'phenology_date') -> None:
    """
    Run the full preprocessing pipeline:
    1. Exclude multicollinear features.
    2. Interpolate time series.
    3. Filter insufficient data.
    4. Mask missing phenology labels.
    """
    logger.info(f"Loading data from {input_path}")
    df = load_csv(input_path)
    
    logger.info("Excluding multicollinear features...")
    df = exclude_multicollinear_features(df)
    
    logger.info("Interpolating time series...")
    df, excluded_rows = interpolate_time_series(df)
    
    logger.info("Filtering insufficient data...")
    df = filter_insufficient_data(df)
    
    logger.info("Masking missing phenology labels...")
    df = mask_missing_phenology_labels(df, phenology_col=phenology_col)
    
    logger.info(f"Saving processed data to {output_path}")
    save_csv(df, output_path)
    
    logger.info(f"Preprocessing complete. Excluded {excluded_rows} rows due to large gaps.")

def main():
    setup_logging()
    # Default paths can be overridden by config or args in a real implementation
    input_file = "data/processed/raw_aligned_data.csv"
    output_file = "data/processed/preprocessed_data_masked.csv"
    
    # Check if input exists to avoid errors in dry runs if file missing
    if not Path(input_file).exists():
        logger.error(f"Input file {input_file} not found. Cannot run preprocessing.")
        # In a real CI run, this would fail the job.
        # For this implementation, we assume the file exists as per pipeline flow.
        return
    
    run_preprocessing(input_file, output_file)

if __name__ == "__main__":
    main()
