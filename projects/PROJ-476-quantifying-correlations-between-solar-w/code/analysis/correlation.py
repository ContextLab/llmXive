import os
import pandas as pd
import numpy as np
from scipy import stats
from datetime import timedelta
from typing import Dict, List, Tuple, Optional
from code import logger
from code.config import ACE_VARS, NOAA_VARS

def load_synced_data(filepath: Optional[str] = None) -> pd.DataFrame:
    """
    Load the synchronized dataset from disk.
    
    Supports two calling conventions:
    1. load_synced_data() -> loads default path from config (for internal use/tests)
    2. load_synced_data(filepath) -> loads from provided path (for main.py, viz)
    
    Args:
        filepath: Optional path to the synced CSV. If None, uses default.
        
    Returns:
        pd.DataFrame: The loaded dataset with timestamp as index.
    """
    if filepath is None:
        # Default path if no argument provided (used in some internal calls)
        default_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'processed', 'synced.csv')
        filepath = default_path
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Synced data file not found at: {filepath}")
    
    logger.info(f"Loading synced data from {filepath}")
    df = pd.read_csv(filepath, parse_dates=['timestamp'])
    df.set_index('timestamp', inplace=True)
    return df

def shift_series(series: pd.Series, lag_hours: int) -> pd.Series:
    """
    Shift a time series forward by a specified number of hours to align
    with the solar wind composition (predictor) at time t.
    
    This function shifts the geomagnetic index series forward (positive lag)
    so that the value at time t corresponds to the solar wind condition
    that occurred 'lag_hours' earlier.
    
    Args:
        series: The time series to shift (e.g., Kp or Dst).
        lag_hours: The number of hours to shift forward. Positive values
                  shift the series forward in time (index t gets value from t - lag).
                  
    Returns:
        pd.Series: The shifted series. The beginning of the series will contain
                  NaNs corresponding to the lag period, which should be dropped
                  before correlation calculation to prevent bias.
    """
    if lag_hours == 0:
        return series.copy()
    
    # Create a copy to avoid modifying the original
    shifted = series.copy()
    
    if lag_hours > 0:
        # Shift forward: value at time t comes from t - lag_hours
        # This aligns the geomagnetic index with the solar wind that caused it
        # Example: if lag=24, the Kp at 12:00 today is aligned with solar wind at 12:00 yesterday
        shifted.index = shifted.index + pd.Timedelta(hours=lag_hours)
    else:
        # Negative lag: shift backward
        shifted.index = shifted.index + pd.Timedelta(hours=lag_hours)
    
    # Sort by index to ensure correct ordering after shift
    shifted = shifted.sort_index()
    
    return shifted

def compute_correlations_at_lag(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    lag_hours: int,
    method: str = 'pearson'
) -> Tuple[float, float]:
    """
    Compute correlation between two series at a specific lag.
    
    Args:
        df: DataFrame with datetime index.
        x_col: Name of the composition parameter column (predictor).
        y_col: Name of the geomagnetic index column (response).
        lag_hours: Lag in hours to apply to y_col.
        method: 'pearson' or 'spearman'.
                
    Returns:
        Tuple of (correlation_coefficient, p_value).
    """
    # Shift the response series
    y_shifted = shift_series(df[y_col], lag_hours)
    
    # Align the two series and drop NaNs
    valid_mask = y_shifted.notna() & df[x_col].notna()
    x_aligned = df[x_col][valid_mask]
    y_aligned = y_shifted[valid_mask]
    
    if len(x_aligned) < 2:
        logger.warning(f"Insufficient data for correlation at lag {lag_hours}h: {len(x_aligned)} points")
        return np.nan, np.nan
    
    if method == 'pearson':
        corr, p_val = stats.pearsonr(x_aligned, y_aligned)
    elif method == 'spearman':
        corr, p_val = stats.spearmanr(x_aligned, y_aligned)
    else:
        raise ValueError(f"Unknown method: {method}")
    
    return corr, p_val

def run_correlation_analysis(
    df: pd.DataFrame,
    lags: List[int],
    output_path: str
) -> None:
    """
    Run the full lagged correlation analysis for all composition parameters
    and geomagnetic indices.
    
    Args:
        df: The synchronized DataFrame.
        lags: List of lag hours to test.
        output_path: Path to write the results CSV.
    """
    logger.info(f"Starting correlation analysis with {len(lags)} lags")
    
    results = []
    
    composition_vars = ['proton_density', 'temperature', 'helium_abundance']
    geomagnetic_vars = ['Kp', 'Dst']
    
    for comp_var in composition_vars:
        for geom_var in geomagnetic_vars:
            for lag in lags:
                try:
                    r_pearson, p_raw = compute_correlations_at_lag(
                        df, comp_var, geom_var, lag, method='pearson'
                    )
                    r_spearman, _ = compute_correlations_at_lag(
                        df, comp_var, geom_var, lag, method='spearman'
                    )
                    
                    results.append({
                        'composition_parameter': comp_var,
                        'geomagnetic_index': geom_var,
                        'lag_hours': lag,
                        'pearson_r': r_pearson,
                        'spearman_rho': r_spearman,
                        'p_raw': p_raw
                    })
                except Exception as e:
                    logger.error(f"Error computing correlation for {comp_var} vs {geom_var} at lag {lag}h: {e}")
                    results.append({
                        'composition_parameter': comp_var,
                        'geomagnetic_index': geom_var,
                        'lag_hours': lag,
                        'pearson_r': np.nan,
                        'spearman_rho': np.nan,
                        'p_raw': np.nan
                    })
    
    # Convert to DataFrame and write
    results_df = pd.DataFrame(results)
    
    # Calculate Bonferroni correction (fixed divisor of 30)
    total_tests = 30
    results_df['p_bonferroni'] = results_df['p_raw'].apply(lambda p: min(p * total_tests, 1.0) if not pd.isna(p) else np.nan)
    results_df['significance_flag'] = results_df['p_bonferroni'] < 0.05
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    results_df.to_csv(output_path, index=False)
    logger.info(f"Correlation results written to {output_path}")
    
    return results_df