"""
Stratified sampling utilities for time-series datasets.

This module implements stratified random sampling to select a balanced subset
of M4 and UCI series, ensuring representation across frequencies (for M4)
and load profiles (for UCI).
"""
import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple, Union
from pathlib import Path
import os

# Import from project utilities
from utils.logger import get_logger
from config import PROJECT_ROOT, DATA_PROCESSED_DIR

logger = get_logger(__name__)


def _get_m4_strata(series_df: pd.DataFrame) -> pd.Series:
    """
    Determine strata for M4 data based on 'frequency' column.
    
    Args:
        series_df: DataFrame containing M4 series with 'frequency' column.
        
    Returns:
        Series of strata labels.
    """
    if 'frequency' not in series_df.columns:
        raise ValueError("M4 data must contain a 'frequency' column for stratification.")
    return series_df['frequency']


def _get_uci_strata(series_df: pd.DataFrame) -> pd.Series:
    """
    Determine strata for UCI data based on load profile characteristics.
    
    For UCI Electricity, we stratify by the mean load level (Low/Medium/High)
    to ensure balanced representation of different consumption patterns.
    
    Args:
        series_df: DataFrame containing UCI series with 'mean_load' or similar metric.
        
    Returns:
        Series of strata labels.
    """
    if 'mean_load' not in series_df.columns:
        # Fallback: calculate mean if not present but 'value' exists
        if 'value' in series_df.columns:
            mean_loads = series_df.groupby('series_id')['value'].mean()
            series_df = series_df.merge(
                mean_loads.rename('mean_load'), 
                on='series_id', 
                how='left'
            )
        else:
            raise ValueError("UCI data must contain a 'mean_load' column or 'value' column for stratification.")
    
    # Create bins: Low, Medium, High
    # Use quantiles to ensure balanced strata sizes
    q_low = series_df['mean_load'].quantile(0.33)
    q_high = series_df['mean_load'].quantile(0.66)
    
    def categorize(x):
        if x <= q_low:
            return 'Low'
        elif x <= q_high:
            return 'Medium'
        else:
            return 'High'
    
    return series_df['mean_load'].apply(categorize)


def stratified_sampler(
    df: pd.DataFrame,
    dataset_type: str,
    n_samples: int,
    random_state: Optional[int] = None,
    strata_column: Optional[str] = None
) -> pd.DataFrame:
    """
    Perform stratified random sampling on a time-series dataset.
    
    Ensures that the selected subset is representative of the underlying
    distribution of frequencies (M4) or load profiles (UCI).
    
    Args:
        df: Input DataFrame containing time-series data.
            For M4: Must have 'series_id' and 'frequency' columns.
            For UCI: Must have 'series_id' and 'mean_load' (or 'value') columns.
        dataset_type: Type of dataset ('M4' or 'UCI').
        n_samples: Total number of series to sample.
        random_state: Random seed for reproducibility.
        strata_column: Optional override for the strata column name.
            
    Returns:
        DataFrame containing the sampled series (preserving original rows per series).
        
    Raises:
        ValueError: If dataset_type is invalid or required columns are missing.
        RuntimeError: If n_samples exceeds available unique series.
    """
    if random_state is not None:
        np.random.seed(random_state)
        
    if dataset_type not in ['M4', 'UCI']:
        raise ValueError(f"dataset_type must be 'M4' or 'UCI', got '{dataset_type}'")
    
    # Identify unique series
    if 'series_id' not in df.columns:
        raise ValueError("Input DataFrame must contain 'series_id' column.")
    
    unique_series = df['series_id'].unique()
    n_total = len(unique_series)
    
    if n_samples > n_total:
        raise RuntimeError(f"Requested {n_samples} samples but only {n_total} unique series available.")
    
    # Determine strata
    if strata_column:
        strata = df[strata_column]
    else:
        if dataset_type == 'M4':
            strata = _get_m4_strata(df)
        else:  # UCI
            strata = _get_uci_strata(df)
    
    # Group by series and strata to get strata distribution per series
    series_strata = df[['series_id', strata.name]].drop_duplicates()
    
    # Calculate proportion of each strata
    strata_counts = series_strata[strata.name].value_counts()
    strata_proportions = strata_counts / strata_counts.sum()
    
    # Calculate samples per strata
    samples_per_strata = (strata_proportions * n_samples).round().astype(int)
    
    # Adjust for rounding errors to ensure exact n_samples
  #   current_sum = samples_per_strata.sum()
  #   diff = n_samples - current_sum
  #   if diff != 0:
  #       # Add or remove from largest strata
  #       largest_strata = samples_per_strata.idxmax()
  #       samples_per_strata[largest_strata] += diff
    
    logger.info(f"Stratified sampling: {n_samples} samples from {n_total} series across {len(strata_counts)} strata.")
    logger.debug(f"Strata distribution: {samples_per_strata.to_dict()}")
    
    selected_series = []
    
    for stratum, count in samples_per_strata.items():
        if count == 0:
            continue
        
        # Get series in this stratum
        stratum_series = series_strata[series_strata[strata.name] == stratum]['series_id'].unique()
        
        if len(stratum_series) < count:
            # Take all available if not enough
            sampled = stratum_series
            logger.warning(f"Stratum '{stratum}' has only {len(stratum_series)} series, taking all.")
        else:
            # Random sample
            sampled = np.random.choice(stratum_series, size=count, replace=False)
        
        selected_series.extend(sampled)
    
    # Filter original DataFrame to selected series
    result_df = df[df['series_id'].isin(selected_series)].copy()
    
    logger.info(f"Final sample size: {result_df['series_id'].nunique()} unique series.")
    
    return result_df


def save_sample_metadata(
    sample_df: pd.DataFrame,
    dataset_type: str,
    output_dir: Optional[Path] = None
) -> Path:
    """
    Save metadata about the stratified sample to a CSV file.
    
    Args:
        sample_df: The sampled DataFrame.
        dataset_type: Type of dataset ('M4' or 'UCI').
        output_dir: Directory to save metadata. Defaults to DATA_PROCESSED_DIR.
        
    Returns:
        Path to the saved metadata file.
    """
    if output_dir is None:
        output_dir = DATA_PROCESSED_DIR
        
    os.makedirs(output_dir, exist_ok=True)
    
    # Calculate strata distribution
    if dataset_type == 'M4':
        strata_col = 'frequency'
    else:
        # Recalculate mean_load if not present
        if 'mean_load' not in sample_df.columns and 'value' in sample_df.columns:
            mean_loads = sample_df.groupby('series_id')['value'].mean()
            sample_df = sample_df.merge(mean_loads.rename('mean_load'), on='series_id')
        strata_col = 'mean_load'
    
    if strata_col not in sample_df.columns:
        raise ValueError(f"Cannot calculate metadata: missing column '{strata_col}'")
    
    # Get unique series and their strata
    series_info = sample_df[['series_id', strata_col]].drop_duplicates()
    
    # Add strata category
    if dataset_type == 'M4':
        series_info['strata'] = series_info[strata_col]
    else:
        q_low = series_info[strata_col].quantile(0.33)
        q_high = series_info[strata_col].quantile(0.66)
        def categorize(x):
            if x <= q_low: return 'Low'
            elif x <= q_high: return 'Medium'
            else: return 'High'
        series_info['strata'] = series_info[strata_col].apply(categorize)
    
    # Count per strata
    strata_counts = series_info['strata'].value_counts().sort_index()
    
    # Save to CSV
    metadata_path = output_dir / f"sample_metadata_{dataset_type.lower()}.csv"
    series_info.to_csv(metadata_path, index=False)
    
    logger.info(f"Sample metadata saved to {metadata_path}")
    logger.info(f"Strata distribution: {strata_counts.to_dict()}")
    
    return metadata_path
