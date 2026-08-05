"""
Correlation analysis module for solar wind and geomagnetic indices.
Implements lagged correlation, significance testing, and result aggregation.
"""
import os
import pandas as pd
import numpy as np
from scipy import stats
from datetime import timedelta
from typing import Dict, List, Tuple, Optional
from code import logger
from code.config import TRAIN_START, TRAIN_END, TEST_START, TEST_END
from code.analysis.neff import calculate_effective_sample_size_neff

# Constants
DEFAULT_LAGS = [0, 1, 2, 3, 6, 12, 24, 48, 72]
BONFERRONI_DIVISOR = 30  # Fixed global divisor for family-wise error rate

def load_synced_data(data_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load the synchronized dataset.
    
    Supports two calling patterns:
    1. load_synced_data() -> loads default path from config
    2. load_synced_data(data_path) -> loads from specified path
    
    Args:
        data_path: Optional path to the synced CSV file. If None, uses default.
        
    Returns:
        pd.DataFrame: The loaded dataset
    """
    if data_path is None:
        # Default path if no argument provided
        data_path = os.path.join("data", "processed", "synced.csv")
    
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Synced data file not found at {data_path}")
    
    logger.info(f"Loading synced data from {data_path}")
    df = pd.read_csv(data_path, parse_dates=['timestamp'])
    return df

def shift_series(series: pd.Series, lag_hours: int) -> pd.Series:
    """
    Shift a time series forward by lag_hours to align with predictor.
    
    This shifts the geomagnetic index (response) forward so that the value
    at time t corresponds to the solar wind composition at time t - lag_hours.
    
    Args:
        series: The time series to shift
        lag_hours: Number of hours to shift forward
        
    Returns:
        pd.Series: The shifted series with NaNs at the beginning
    """
    if lag_hours == 0:
        return series
    
    # Shift forward by creating new index
    shifted = series.copy()
    shifted.index = shifted.index + pd.Timedelta(hours=lag_hours)
    
    # Reindex to original timeline, introducing NaNs at the start
    original_index = series.index
    result = shifted.reindex(original_index)
    
    logger.debug(f"Shifted series by {lag_hours} hours, introduced {result.isna().sum()} NaNs")
    return result

def compute_correlations_at_lag(df: pd.DataFrame, 
                                x_col: str, 
                                y_col: str, 
                                lag_hours: int) -> Dict[str, float]:
    """
    Compute Pearson and Spearman correlations at a specific lag.
    
    Args:
        df: The synchronized dataframe
        x_col: Name of the composition parameter column
        y_col: Name of the geomagnetic index column
        lag_hours: The temporal lag in hours
        
    Returns:
        Dict containing pearson_r, spearman_rho, and n_effective
    """
    # Shift the response variable (y)
    y_shifted = shift_series(df[y_col], lag_hours)
    
    # Drop NaN pairs
    valid_mask = ~(y_shifted.isna() | df[x_col].isna())
    x_valid = df.loc[valid_mask, x_col]
    y_valid = y_shifted.loc[valid_mask]
    
    n_valid = len(x_valid)
    if n_valid < 10:
        logger.warning(f"Insufficient valid pairs ({n_valid}) for correlation at lag {lag_hours}")
        return {
            'pearson_r': np.nan,
            'spearman_rho': np.nan,
            'n_effective': np.nan,
            'n_raw': n_valid
        }
    
    # Compute Pearson correlation
    pearson_r, _ = stats.pearsonr(x_valid, y_valid)
    
    # Compute Spearman correlation
    spearman_rho, _ = stats.spearmanr(x_valid, y_valid)
    
    # Compute effective sample size using the response series
    # (Note: Neff is typically computed on the residuals or the series itself)
    # We use the shifted y series for Neff calculation
    n_eff = calculate_effective_sample_size_neff(y_valid)
    
    return {
        'pearson_r': pearson_r,
        'spearman_rho': spearman_rho,
        'n_effective': n_eff,
        'n_raw': n_valid
    }

def compute_p_value_adjusted(r: float, n_eff: float) -> float:
    """
    Compute the two-tailed p-value for a correlation coefficient using effective sample size.
    
    Uses the t-statistic formula: t = r * sqrt((n_eff - 2) / (1 - r^2))
    and calculates the two-tailed p-value using scipy.stats.t.sf.
    
    Args:
        r: Pearson correlation coefficient
        n_eff: Effective sample size
        
    Returns:
        float: Two-tailed p-value
    """
    if np.isnan(r) or np.isnan(n_eff) or n_eff <= 2:
        return np.nan
    
    # Handle edge case where r is exactly 1 or -1
    if abs(r) >= 1.0:
        return 0.0
    
    # Calculate t-statistic
    t_stat = r * np.sqrt((n_eff - 2) / (1 - r**2))
    
    # Calculate two-tailed p-value using survival function
    # df = n_eff - 2
    p_value = 2 * stats.t.sf(np.abs(t_stat), df=n_eff - 2)
    
    return p_value

def apply_bonferroni_correction(p_raw: float, num_tests: int = BONFERRONI_DIVISOR) -> float:
    """
    Apply Bonferroni correction to a p-value.
    
    Args:
        p_raw: Raw p-value
        num_tests: Number of tests in the family (default 30)
        
    Returns:
        float: Bonferroni-corrected p-value (capped at 1.0)
    """
    p_corrected = p_raw * num_tests
    return min(p_corrected, 1.0)

def run_correlation_analysis(df: pd.DataFrame, 
                             composition_params: List[str],
                             geomagnetic_indices: List[str],
                             lags: List[int],
                             output_path: str) -> pd.DataFrame:
    """
    Run the full lagged correlation analysis and write results.
    
    Args:
        df: The synchronized dataframe
        composition_params: List of composition parameter column names
        geomagnetic_indices: List of geomagnetic index column names
        lags: List of lag hours to test
        output_path: Path to write the results CSV
        
    Returns:
        pd.DataFrame: The correlation results
    """
    results = []
    
    logger.info(f"Starting correlation analysis for {len(composition_params)} parameters, "
               f"{len(geomagnetic_indices)} indices, {len(lags)} lags")
    
    for comp_param in composition_params:
        for geom_index in geomagnetic_indices:
            for lag in lags:
                logger.debug(f"Computing {comp_param} vs {geom_index} at lag {lag}h")
                
                try:
                    corr_stats = compute_correlations_at_lag(
                        df, comp_param, geom_index, lag
                    )
                    
                    r = corr_stats['pearson_r']
                    rho = corr_stats['spearman_rho']
                    n_eff = corr_stats['n_effective']
                    
                    # Compute adjusted p-value
                    p_raw = compute_p_value_adjusted(r, n_eff)
                    p_bonferroni = apply_bonferroni_correction(p_raw)
                    
                    # Determine significance flag
                    significance_flag = p_bonferroni < 0.05
                    
                    results.append({
                        'composition_parameter': comp_param,
                        'geomagnetic_index': geom_index,
                        'lag_hours': lag,
                        'pearson_r': r,
                        'spearman_rho': rho,
                        'p_raw': p_raw,
                        'p_bonferroni': p_bonferroni,
                        'significance_flag': significance_flag
                    })
                    
                except Exception as e:
                    logger.error(f"Error computing correlation for {comp_param} vs {geom_index} at lag {lag}h: {e}")
                    results.append({
                        'composition_parameter': comp_param,
                        'geomagnetic_index': geom_index,
                        'lag_hours': lag,
                        'pearson_r': np.nan,
                        'spearman_rho': np.nan,
                        'p_raw': np.nan,
                        'p_bonferroni': np.nan,
                        'significance_flag': False
                    })
    
    # Create DataFrame
    results_df = pd.DataFrame(results)
    
    # Write to CSV
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    results_df.to_csv(output_path, index=False)
    logger.info(f"Correlation results written to {output_path}")
    
    return results_df

def iterate_lagged_pairs(df: pd.DataFrame, lags: List[int]) -> List[Tuple[str, str, int]]:
    """
    Generate all pairs of (composition_param, geomagnetic_index, lag).
    
    Args:
        df: The synchronized dataframe
        lags: List of lag hours to test
        
    Returns:
        List of tuples (comp_param, geom_index, lag)
    """
    # Define standard composition parameters and indices
    composition_params = ['proton_density', 'temperature', 'helium_abundance']
    geomagnetic_indices = ['Kp', 'Dst']
    
    # Filter to only columns present in dataframe
    composition_params = [p for p in composition_params if p in df.columns]
    geomagnetic_indices = [g for g in geomagnetic_indices if g in df.columns]
    
    pairs = []
    for comp in composition_params:
        for geom in geomagnetic_indices:
            for lag in lags:
                pairs.append((comp, geom, lag))
    
    return pairs