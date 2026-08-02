import pandas as pd
import numpy as np
from typing import List, Optional, Tuple, Dict
from pathlib import Path
import logging
from src.lib.utils import load_csv, save_csv, setup_logging

logger = logging.getLogger(__name__)

def exclude_multicollinear_features(df: pd.DataFrame, features_to_exclude: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Remove specified features from the DataFrame to prevent multicollinearity.
    
    Args:
        df: Input DataFrame
        features_to_exclude: List of column names to remove. Defaults to ['gdd_cumulative'].
        
    Returns:
        DataFrame with specified columns removed.
    """
    if features_to_exclude is None:
        features_to_exclude = ['gdd_cumulative']
        
    existing_features = [f for f in features_to_exclude if f in df.columns]
    missing_features = [f for f in features_to_exclude if f not in df.columns]
    
    if missing_features:
        logger.warning(f"Features {missing_features} not found in DataFrame. Skipping.")
        
    if existing_features:
        logger.info(f"Excluding multicollinear features: {existing_features}")
        df = df.drop(columns=existing_features)
        
    return df

def interpolate_time_series(df: pd.DataFrame, date_col: str = 'date', value_cols: Optional[List[str]] = None, max_gap: int = 1) -> pd.DataFrame:
    """
    Interpolate missing values in time series data with linear interpolation.
    Excludes rows if gaps exceed max_gap consecutive missing values.
    
    Args:
        df: Input DataFrame with a date column
        date_col: Name of the date column
        value_cols: Columns to interpolate. If None, all numeric columns except date_col are used.
        max_gap: Maximum number of consecutive missing values allowed for interpolation.
        
    Returns:
        DataFrame with interpolated values and rows with excessive gaps removed.
    """
    df = df.copy()
    
    if date_col not in df.columns:
        raise ValueError(f"Date column '{date_col}' not found in DataFrame")
        
    df[date_col] = pd.to_datetime(df[date_col])
    df = df.sort_values(by=date_col).reset_index(drop=True)
    
    if value_cols is None:
        value_cols = df.select_dtypes(include=[np.number]).columns.drop(date_col, errors='ignore').tolist()
        
    if not value_cols:
        logger.warning("No numeric columns found to interpolate.")
        return df
        
    # Identify gaps
    mask = df[value_cols].isna()
    
    # Count consecutive gaps per column
    for col in value_cols:
        if col not in mask.columns:
            continue
            
        # Create a group for consecutive True values
        groups = (~mask[col]).cumsum()
        # Count size of True groups
        gap_counts = mask[col].groupby(groups).transform('sum')
        
        # Mark rows with excessive gaps
        excessive = (mask[col]) & (gap_counts > max_gap)
        
        if excessive.any():
            logger.warning(f"Column '{col}' has {excessive.sum()} rows with gaps > {max_gap}. Excluding them.")
            df = df[~excessive]
            
    # Perform interpolation on remaining data
    for col in value_cols:
        if col in df.columns:
            df[col] = df[col].interpolate(method='linear', limit=max_gap)
            
    # Drop rows that are still NaN after interpolation
    rows_to_drop = df[value_cols].isna().any(axis=1)
    if rows_to_drop.any():
        logger.warning(f"Dropping {rows_to_drop.sum()} rows that still have missing values after interpolation.")
        df = df[~rows_to_drop]
        
    return df.reset_index(drop=True)

def filter_insufficient_data(df: pd.DataFrame, coverage_threshold: float = 0.8, obs_col: Optional[str] = None) -> pd.DataFrame:
    """
    Filter out sites with insufficient cloud-free coverage or observations.
    
    Args:
        df: Input DataFrame with site and observation columns
        coverage_threshold: Minimum required coverage fraction (default 0.8)
        obs_col: Column name representing observation count or coverage. 
                If None, calculates coverage based on non-null rows per site.
                
    Returns:
        DataFrame with insufficient sites removed.
    """
    if 'site_id' not in df.columns:
        logger.warning("No 'site_id' column found. Skipping site filtering.")
        return df
        
    if obs_col:
        if obs_col not in df.columns:
            logger.warning(f"Observation column '{obs_col}' not found. Skipping filtering based on it.")
            # Fallback to standard coverage calculation
            obs_col = None
            
    if obs_col:
        # Calculate coverage based on the specific observation column
        site_stats = df.groupby('site_id')[obs_col].agg(['mean', 'count']).reset_index()
        # Assuming obs_col represents a coverage metric directly or count
        # If it's a count, we need a max expected count to calculate ratio. 
        # For now, assuming it's a ratio or we filter by count if specified differently.
        # Let's assume obs_col is a boolean or ratio. If it's count, we need a reference.
        # Given the task context, let's assume we check if the mean coverage > threshold
        valid_sites = site_stats[site_stats['mean'] >= coverage_threshold]['site_id'].tolist()
    else:
        # Standard approach: count non-null rows per site vs total rows
        total_rows_per_site = df.groupby('site_id').size()
        non_null_rows_per_site = df.groupby('site_id').apply(lambda x: x.notna().sum(axis=1).mean()) # This might be wrong if multiple cols
        
        # Better: count rows where at least one critical value exists? 
        # Or count total rows vs rows with all critical features present?
        # Let's assume we check the ratio of non-null rows in a specific critical column or overall.
        # Using 'date' as a proxy for row presence? No.
        # Let's count non-null in 'site_id' group vs total group size?
        # Actually, the task says "zero cloud-free observations". 
        # Let's assume we have a 'cloud_free' or similar boolean, or we count non-null in target features.
        # Since we don't know the exact schema, let's count non-null in any numeric feature.
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if not numeric_cols:
            logger.warning("No numeric columns found to assess coverage.")
            return df
            
        # Count rows with at least one valid numeric value per site
        valid_rows = df[numeric_cols].notna().any(axis=1)
        site_valid_counts = df[valid_rows].groupby('site_id').size()
        site_total_counts = df.groupby('site_id').size()
        
        coverage = site_valid_counts / site_total_counts
        valid_sites = coverage[coverage >= coverage_threshold].index.tolist()
        
    missing_sites = set(df['site_id'].unique()) - set(valid_sites)
    if missing_sites:
        logger.warning(f"Filtering out {len(missing_sites)} sites with insufficient data: {missing_sites}")
        
    return df[df['site_id'].isin(valid_sites)].reset_index(drop=True)

def mask_missing_phenology_labels(df: pd.DataFrame, phenology_cols: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Handle missing phenology labels by masking rows during training.
    This function does NOT impute values. Instead, it marks rows with missing labels
    so they can be excluded from the training target but potentially kept for 
    feature analysis if needed (though typically excluded from supervised training).
    
    Args:
        df: Input DataFrame containing phenology observation columns
        phenology_cols: List of column names representing phenology labels (e.g., 'budburst_date', 'flowering_date').
                       If None, attempts to infer columns containing 'date' or 'phenology'.
                       
    Returns:
        DataFrame with an additional column 'has_phenology_label' (bool) indicating 
        if the row has valid labels for training. Rows with False can be filtered 
        before model training.
    """
    df = df.copy()
    
    if phenology_cols is None:
        # Heuristic: look for columns with 'date' or 'phenology' in the name
        phenology_cols = [col for col in df.columns if ('date' in col.lower() or 'phenology' in col.lower()) and col != 'date']
        if not phenology_cols:
            logger.warning("Could not automatically detect phenology columns. Assuming 'phenology_label' or similar. No masking applied.")
            df['has_phenology_label'] = True
            return df
            
    logger.info(f"Checking phenology labels in columns: {phenology_cols}")
    
    # Check if any of the specified columns are missing
    # A row is valid if it has a non-null value in AT LEAST ONE of the target phenology columns
    # OR if the task implies a specific single label column. 
    # Given "missing phenology labels", we assume we need the target variable for the event.
    # We'll assume if any of the phenology_cols is not null, the row is usable for that specific event.
    # However, for a general "masking" function, we create a boolean mask.
    
    mask = pd.Series(False, index=df.index)
    for col in phenology_cols:
        if col in df.columns:
            mask = mask | df[col].notna()
        else:
            logger.warning(f"Phenology column '{col}' not found in DataFrame.")
            
    df['has_phenology_label'] = mask
    
    missing_count = (~mask).sum()
    if missing_count > 0:
        logger.warning(f"Found {missing_count} rows with missing phenology labels. These rows are marked with has_phenology_label=False.")
    else:
        logger.info("All rows have phenology labels.")
        
    return df

def run_preprocessing(input_path: Path, output_path: Path, config: Dict) -> None:
    """
    Run the full preprocessing pipeline:
    1. Exclude multicollinear features
    2. Interpolate time series
    3. Filter insufficient data
    4. Mask missing phenology labels
    
    Args:
        input_path: Path to input CSV
        output_path: Path to output CSV
        config: Configuration dictionary containing parameters
    """
    logger.info(f"Loading data from {input_path}")
    df = load_csv(input_path)
    
    # 1. Exclude multicollinear features
    exclude_list = config.get('exclude_features', ['gdd_cumulative'])
    df = exclude_multicollinear_features(df, exclude_list)
    
    # 2. Interpolate time series
    max_gap = config.get('max_gap', 1)
    date_col = config.get('date_col', 'date')
    df = interpolate_time_series(df, date_col=date_col, max_gap=max_gap)
    
    # 3. Filter insufficient data
    coverage_threshold = config.get('coverage_threshold', 0.8)
    df = filter_insufficient_data(df, coverage_threshold=coverage_threshold)
    
    # 4. Mask missing phenology labels
    phenology_cols = config.get('phenology_cols', None)
    df = mask_missing_phenology_labels(df, phenology_cols=phenology_cols)
    
    # Save the processed data
    logger.info(f"Saving processed data to {output_path}")
    save_csv(df, output_path)
    
    logger.info(f"Preprocessing complete. Rows before: {len(df)}, Rows after (with labels): {df['has_phenology_label'].sum()}")

def main():
    """Main entry point for preprocessing script."""
    setup_logging()
    logger.info("Starting preprocessing pipeline...")
    
    # Load config (simplified for script execution, normally from config.py)
    from src.config import get_config
    cfg = get_config()
    
    input_file = cfg.get('paths', {}).get('processed_data_input', 'data/processed/aligned_data.csv')
    output_file = cfg.get('paths', {}).get('processed_data_output', 'data/processed/preprocessed_data.csv')
    
    # Ensure paths are Path objects
    input_path = Path(input_file)
    output_path = Path(output_file)
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
        
    run_preprocessing(input_path, output_path, cfg)
    logger.info("Preprocessing pipeline finished.")

if __name__ == "__main__":
    main()
