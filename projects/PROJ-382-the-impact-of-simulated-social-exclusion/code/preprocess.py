import json
from pathlib import Path
from typing import Tuple, Dict, Any, Optional
import pandas as pd
import numpy as np
import logging

from logging_config import get_project_logger

logger = get_project_logger(__name__)

def handle_missing_values(df: pd.DataFrame, threshold: float = 0.05) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Handle missing values in the DataFrame.
    
    Args:
        df: Input DataFrame
        threshold: Threshold for missing values (0.05 = 5%)
        
    Returns:
        Tuple of (cleaned DataFrame, imputation log)
    """
    log_data = {
        'total_rows': len(df),
        'columns_imputed': {},
        'rows_excluded': 0
    }
    
    # Check missing percentage per column
    missing_pct = df.isnull().mean()
    
    for col in df.columns:
        if missing_pct[col] > 0:
            if missing_pct[col] < threshold:
                # Median imputation
                median_val = df[col].median()
                df[col] = df[col].fillna(median_val)
                log_data['columns_imputed'][col] = {
                    'method': 'median',
                    'value': float(median_val),
                    'count': int(df.isnull().sum()[col])
                }
            else:
                # Exclude rows with missing values
                initial_len = len(df)
                df = df.dropna(subset=[col])
                excluded = initial_len - len(df)
                log_data['rows_excluded'] += excluded
                logger.warning(f"Excluded {excluded} rows due to missing values in {col}")
    
    log_data['final_rows'] = len(df)
    return df, log_data

def split_pools(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split data into causal and associational pools.
    
    Args:
        df: Input DataFrame with 'randomized' column
        
    Returns:
        Tuple of (causal_pool, associational_pool)
    """
    causal = df[df['randomized'] == True].copy()
    associational = df[df['randomized'] != True].copy()
    
    logger.info(f"Split pools: Causal={len(causal)}, Associational={len(associational)}")
    return causal, associational

def filter_small_samples(df: pd.DataFrame, min_size: int = 5) -> pd.DataFrame:
    """
    Filter out datasets with small sample sizes in exclusion group.
    
    Args:
        df: Input DataFrame
        min_size: Minimum sample size
        
    Returns:
        Filtered DataFrame
    """
    # Group by dataset source and check exclusion group size
    # Assuming 'condition' is 1 for exclusion
    exclusion_counts = df[df['condition'] == 1].groupby('dataset_id').size()
    valid_datasets = exclusion_counts[exclusion_counts >= min_size].index.tolist()
    
    filtered = df[df['dataset_id'].isin(valid_datasets)]
    excluded_count = len(df) - len(filtered)
    
    if excluded_count > 0:
        logger.info(f"Excluded {excluded_count} rows from datasets with <{min_size} exclusion samples")
        
    return filtered
