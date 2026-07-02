"""
Robustness analysis module for leave-one-out cross-validation.

This module implements the logic to assess the stability of correlation
coefficients by iteratively removing one sample at a time and recalculating
the metric.
"""

import os
import logging
import pandas as pd
import numpy as np
from typing import Tuple, Optional
from scipy.stats import pearsonr

logger = logging.getLogger(__name__)


def calculate_correlation(x: pd.Series, y: pd.Series) -> float:
    """
    Calculate Pearson correlation coefficient.
    
    Args:
        x: Series of x values
        y: Series of y values
        
    Returns:
        Pearson correlation coefficient r.
    """
    # Handle cases with insufficient data points
    if len(x) < 2:
        return 0.0
        
    r, _ = pearsonr(x, y)
    return r


def perform_leave_one_out_cv(
    data: pd.DataFrame,
    x_col: str,
    y_col: str,
    output_path: Optional[str] = None
) -> pd.DataFrame:
    """
    Perform leave-one-out cross-validation to assess correlation stability.
    
    For each sample in the dataset:
    1. Exclude the sample.
    2. Calculate the correlation coefficient (r_loo) on the remaining data.
    3. Calculate the delta (Δr) = |r_full - r_loo|.
    
    Args:
        data: DataFrame containing the analysis dataset.
        x_col: Name of the column for the independent variable (spatial metric).
        y_col: Name of the column for the dependent variable (PCE).
        output_path: Optional path to write the results CSV.
        
    Returns:
        DataFrame with columns: sample_id, r_loo, delta_r.
    """
    if data.empty:
        raise ValueError("Input data cannot be empty.")
        
    if x_col not in data.columns or y_col not in data.columns:
        raise ValueError(f"Columns '{x_col}' and/or '{y_col}' not found in data.")
        
    # Calculate full correlation
    r_full = calculate_correlation(data[x_col], data[y_col])
    logger.info(f"Full dataset correlation (r_full): {r_full:.4f}")
    
    results = []
    
    # Iterate over each sample
    for idx, row in data.iterrows():
        # Create mask to exclude current sample
        mask = data.index != idx
        df_loo = data.loc[mask]
        
        # Check if we have enough data points
        if len(df_loo) < 2:
            logger.warning(f"Not enough data points to calculate correlation after removing {row['sample_id']}.")
            r_loo = np.nan
        else:
            r_loo = calculate_correlation(df_loo[x_col], df_loo[y_col])
        
        # Calculate delta r
        if not np.isnan(r_loo):
            delta_r = abs(r_full - r_loo)
        else:
            delta_r = np.nan
            
        results.append({
            'sample_id': row['sample_id'],
            'r_loo': r_loo,
            'delta_r': delta_r
        })
        
    result_df = pd.DataFrame(results)
    
    # Write to file if path provided
    if output_path:
        # Ensure directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        result_df.to_csv(output_path, index=False)
        logger.info(f"LOO results written to {output_path}")
        
    return result_df