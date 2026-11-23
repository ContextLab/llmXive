"""
Pettitt test implementation for distribution shift detection.

This module implements the Pettitt test, a non-parametric change point detection
method, with rolling window support to match the MMD detector configuration.

The Pettitt test is a rank-based test for detecting a single change point in a
time series. It is particularly useful for detecting shifts in the location
(mean or median) of a distribution.

Key features:
- Rolling window implementation with configurable window_size and stride
- Matches MMD detector window configuration (window_size=12, stride=1)
- Handles edge cases (constant series, small windows)
- Returns p-values for statistical significance
"""

import os
import sys
import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def pettitt_statistic(x: np.ndarray) -> Tuple[float, float]:
    """
    Compute the Pettitt statistic and p-value for a time series.
    
    The Pettitt test is a non-parametric test for detecting a single change point
    in the location (mean or median) of a time series. It is based on the Mann-Whitney
    U statistic and is robust to outliers and non-normal distributions.
    
    Parameters
    ----------
    x : np.ndarray
        1D array of time series data.
        
    Returns
    -------
    tuple
        (statistic, p_value) where:
        - statistic: The Pettitt statistic (K)
        - p_value: Approximate p-value for the test
        
    Raises
    ------
    ValueError
        If the input array has zero variance or is too small.
        
    Notes
    -----
    The Pettitt statistic is computed as:
        K = max|U_t|
    where U_t is the Mann-Whitney U statistic at time t.
    
    The approximate p-value is computed using:
        p ≈ 2 * exp(-6 * K^2 / (n^3 + n^2))
    where n is the sample size.
    
    References
    ----------
    .. [1] Pettitt, A. N. (1979). A non-parametric approach to the change-point problem.
           Journal of the Royal Statistical Society. Series C (Applied Statistics),
           28(2), 126-135.
    """
    n = len(x)
    
    # Check for minimum sample size
    if n < 2:
        raise ValueError("Pettitt test requires at least 2 data points")
    
    # Check for constant series (zero variance)
    if np.std(x) == 0:
        raise ValueError("Zero variance detected in window; cannot compute Pettitt statistic")
    
    # Compute the Pettitt statistic
    # U_t = sum_{i=1}^t sum_{j=t+1}^n sign(x_i - x_j)
    # K = max|U_t|
    
    # Precompute the sign matrix for efficiency
    # sign(x_i - x_j) for all pairs
    sign_matrix = np.sign(x[:, np.newaxis] - x[np.newaxis, :])
    
    # Compute U_t for each t from 1 to n-1
    # U_t = sum_{i=1}^t sum_{j=t+1}^n sign(x_i - x_j)
    # This can be computed efficiently using cumulative sums
    
    # Initialize U array
    U = np.zeros(n - 1)
    
    # Compute U_t for each t
    for t in range(1, n):
        # U_t = sum_{i=1}^t sum_{j=t+1}^n sign(x_i - x_j)
        # = sum_{i=1}^t (sum_{j=t+1}^n sign(x_i - x_j))
        # = sum_{i=1}^t (sum_{j=t+1}^n sign(x_i - x_j))
        
        # Using the sign matrix:
        # sum_{j=t+1}^n sign(x_i - x_j) for each i in 1..t
        # = sum of rows 0..t-1, columns t..n-1
        
        U[t-1] = np.sum(sign_matrix[:t, t:])
    
    # Find the maximum absolute value of U_t
    K = np.max(np.abs(U))
    
    # Compute the approximate p-value
    # p ≈ 2 * exp(-6 * K^2 / (n^3 + n^2))
    # This is an approximation for large n
    if n > 10:
        p_value = 2 * np.exp(-6 * K**2 / (n**3 + n**2))
    else:
        # For small n, use a more conservative approximation
        p_value = 2 * np.exp(-6 * K**2 / (n**3))
    
    # Ensure p_value is in valid range
    p_value = max(0.0, min(1.0, p_value))
    
    return K, p_value

def run_pettitt_rolling_window(
    data: pd.DataFrame,
    window_size: int = 12,
    stride: int = 1,
    alpha: float = 0.05
) -> List[Dict]:
    """
    Run the Pettitt test on a rolling window of the time series.
    
    This function applies the Pettitt test to each window of the time series,
    allowing for detection of multiple change points over time.
    
    Parameters
    ----------
    data : pd.DataFrame
        DataFrame with columns 'week_id' and 'ili' (or similar value column).
    window_size : int, default=12
        Size of the rolling window in weeks. Must match MMD detector configuration.
    stride : int, default=1
        Stride between consecutive windows. Must match MMD detector configuration.
    alpha : float, default=0.05
        Significance level for the test.
        
    Returns
    -------
    List[Dict]
        List of dictionaries containing:
        - window_start_idx: Starting index of the window
        - window_end_idx: Ending index of the window
        - window_size: Size of the window
        - statistic: Pettitt statistic for the window
        - p_value: P-value for the test
        - is_significant: Whether the test is significant at level alpha
        - change_point_idx: Index of the detected change point within the window (if significant)
        
    Raises
    ------
    ValueError
        If window_size or stride are invalid, or if data is insufficient.
    """
    # Validate parameters
    if window_size < 2:
        raise ValueError("window_size must be at least 2 for Pettitt test")
    if stride < 1:
        raise ValueError("stride must be at least 1")
    if window_size > len(data):
        raise ValueError(f"window_size ({window_size}) cannot exceed data length ({len(data)})")
    
    # Verify window configuration matches MMD detector
    # This is critical for T043: baseline method alignment
    logger.info(f"Running Pettitt rolling window with window_size={window_size}, stride={stride}")
    logger.info(f"This must match MMD detector configuration for valid comparison")
    
    # Extract the value column (assuming 'ili' or similar)
    value_col = None
    for col in ['ili', 'value', 'y', 'target']:
        if col in data.columns:
            value_col = col
            break
    
    if value_col is None:
        raise ValueError("Could not find value column in data. Expected 'ili', 'value', 'y', or 'target'")
    
    values = data[value_col].values
    n = len(values)
    
    results = []
    
    # Iterate through windows
    for start_idx in range(0, n - window_size + 1, stride):
        end_idx = start_idx + window_size
        window_values = values[start_idx:end_idx]
        
        # Skip windows with NaN values
        if np.any(np.isnan(window_values)):
            logger.warning(f"Skipping window [{start_idx}:{end_idx}] due to NaN values")
            continue
        
        try:
            # Compute Pettitt statistic and p-value
            stat, p_value = pettitt_statistic(window_values)
            
            # Determine if significant
            is_significant = p_value < alpha
            
            # Find the change point index within the window
            # This is the index where |U_t| is maximized
            if len(window_values) > 1:
                # Recompute U values to find the change point
                sign_matrix = np.sign(window_values[:, np.newaxis] - window_values[np.newaxis, :])
                U = np.zeros(len(window_values) - 1)
                for t in range(1, len(window_values)):
                    U[t-1] = np.sum(sign_matrix[:t, t:])
                
                change_point_local = np.argmax(np.abs(U)) + 1  # +1 because U is indexed from 0
                change_point_global = start_idx + change_point_local
            else:
                change_point_global = start_idx
            
            result = {
                'window_start_idx': start_idx,
                'window_end_idx': end_idx,
                'window_size': window_size,
                'statistic': stat,
                'p_value': p_value,
                'is_significant': is_significant,
                'change_point_idx': change_point_global,
                'alpha': alpha
            }
            
            results.append(result)
            
            if is_significant:
                logger.info(f"Significant change point detected at window [{start_idx}:{end_idx}]: "
                            f"stat={stat:.4f}, p={p_value:.4f}")
            
        except ValueError as e:
            logger.warning(f"Error processing window [{start_idx}:{end_idx}]: {e}")
            # Skip this window
            continue
    
    return results

def main():
    """
    Main function to run Pettitt test on real data.
    
    This function loads the processed ILI data, runs the Pettitt rolling window test,
    and saves the results to baselines.csv.
    """
    import yaml
    from main import load_config
    
    # Load configuration
    config = load_config()
    window_size = config.window_size
    stride = config.stride
    alpha = config.alpha
    
    # Load processed data
    processed_data_path = 'data/processed/processed_ili.csv'
    if not os.path.exists(processed_data_path):
        logger.error(f"Processed data not found at {processed_data_path}")
        logger.error("Please run the preprocessing pipeline first")
        sys.exit(1)
    
    data = pd.read_csv(processed_data_path)
    
    # Run Pettitt rolling window test
    results = run_pettitt_rolling_window(
        data,
        window_size=window_size,
        stride=stride,
        alpha=alpha
    )
    
    # Convert results to DataFrame and save
    if results:
        results_df = pd.DataFrame(results)
        output_path = 'data/processed/pettitt_results.csv'
        results_df.to_csv(output_path, index=False)
        logger.info(f"Pettitt results saved to {output_path}")
        
        # Also update baselines.csv if it exists
        baselines_path = 'data/processed/baselines.csv'
        if os.path.exists(baselines_path):
            baselines_df = pd.read_csv(baselines_path)
            # Append Pettitt results
            pettitt_for_baselines = results_df[['window_start_idx', 'window_end_idx', 'statistic']].copy()
            pettitt_for_baselines['method'] = 'pettitt'
            pettitt_for_baselines.rename(columns={
                'window_start_idx': 'week_id',
                'statistic': 'run_length'
            }, inplace=True)
            baselines_df = pd.concat([baselines_df, pettitt_for_baselines], ignore_index=True)
            baselines_df.to_csv(baselines_path, index=False)
            logger.info(f"Updated baselines.csv with Pettitt results")
        else:
            # Create new baselines.csv
            pettitt_for_baselines = results_df[['window_start_idx', 'statistic']].copy()
            pettitt_for_baselines['method'] = 'pettitt'
            pettitt_for_baselines.rename(columns={
                'window_start_idx': 'week_id',
                'statistic': 'run_length'
            }, inplace=True)
            pettitt_for_baselines.to_csv(baselines_path, index=False)
            logger.info(f"Created baselines.csv with Pettitt results")
    else:
        logger.warning("No significant change points detected by Pettitt test")
    
    return results

if __name__ == '__main__':
    main()