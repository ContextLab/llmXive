"""
Pettitt's Test for Change-Point Detection with Rolling Window.

Implements a rolling-window application of Pettitt's test to detect
distribution shifts in time-series data (e.g., ILI surveillance).
"""

import os
import sys
import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional

from exceptions import E_NO_DATA
from logging_setup import setup_logging

# Configure logging
logger = logging.getLogger(__name__)

def pettitt_statistic(x: np.ndarray) -> Tuple[int, float]:
    """
    Compute the Pettitt statistic for a given 1D array x.
    
    The Pettitt test is a non-parametric test for a single change-point.
    It is based on the Mann-Whitney U statistic.
    
    Args:
        x: 1D numpy array of observations.
        
    Returns:
        Tuple of (index_of_max_statistic, max_statistic_value).
        The index is relative to the start of the array (0-based).
    """
    n = len(x)
    if n < 2:
        return 0, 0.0
    
    # Compute the Mann-Whitney U statistic for all possible split points
    # U_t = sum_{i=1}^t sum_{j=t+1}^n sign(x_i - x_j)
    # This can be computed efficiently using cumulative sums of ranks or signs.
    
    # Create a matrix of signs (n x n)
    # sign(x_i - x_j)
    # To avoid O(n^2) memory for large n, we compute iteratively or use vectorization carefully.
    # Given typical window sizes (e.g., 12), O(n^2) is acceptable.
    
    signs = np.sign(x[:, np.newaxis] - x[np.newaxis, :])
    # signs[i, j] = sign(x[i] - x[j])
    # We need sum over i<=t, j>t
    
    # The statistic U_t is the sum of signs[i, j] for i <= t and j > t.
    # This is equivalent to the sum of the upper triangle of the sign matrix
    # if we consider the matrix M where M[i,j] = sign(x_i - x_j).
    # Actually, U_t = sum_{i=1}^t sum_{j=t+1}^n sign(x_i - x_j)
    
    # Let's compute the cumulative sum of the sign matrix rows/cols.
    # A more direct O(n^2) approach for small n:
    max_stat = -np.inf
    max_idx = 0
    
    # Precompute the full sign matrix
    # Note: signs[i, j] is 1 if x[i] > x[j], -1 if x[i] < x[j], 0 if equal.
    # We need sum_{i=0}^{t} sum_{j=t+1}^{n-1} signs[i, j]
    
    # Vectorized computation:
    # Create a mask for i <= t and j > t
    # But t varies.
    # Let's compute the matrix S where S[i, j] = sign(x[i] - x[j])
    # Then U_t = sum(S[0:t+1, t+1:n])
    
    # Since n is small (window size), we can do this loop.
    for t in range(1, n):
        # Sum signs for i in 0..t-1 (inclusive) and j in t..n-1 (inclusive)
        # Note: Python slicing: 0:t means 0..t-1. t:n means t..n-1.
        # But the definition is usually 1..t and t+1..n.
        # In 0-indexed: 0..t-1 and t..n-1.
        # Let's stick to the definition: split after t-th element (1-based index t).
        # So left set has t elements (indices 0 to t-1), right set has n-t elements (indices t to n-1).
        
        # Optimization: sum of a submatrix
        current_stat = np.sum(signs[:t, t:])
        
        if current_stat > max_stat:
            max_stat = current_stat
            max_idx = t
            
    return max_idx, max_stat

def pettitt_p_value(stat: float, n: int) -> float:
    """
    Approximate p-value for the Pettitt statistic.
    
    The asymptotic distribution of the Pettitt statistic K is:
    P(K > k) approx 2 * exp(-6 * k^2 / (n^3 + n^2))
    for large n.
    
    Args:
        stat: The maximum Pettitt statistic (K).
        n: Sample size.
        
    Returns:
        Approximate p-value.
    """
    if n < 4:
        return 1.0
    
    # Asymptotic approximation
    # K = max |U_t|
    # The formula is often given as:
    # P(K > k) = 2 * exp(-6 * k^2 / (n^3 + n^2))
    # Or sometimes: exp(-6 * k^2 / (n^3 + n^2))
    # Let's use the standard approximation from Pettitt (1979)
    
    exponent = -6 * (stat ** 2) / (n ** 3 + n ** 2)
    p_val = 2 * np.exp(exponent)
    
    # Ensure p is in [0, 1]
    return min(max(p_val, 0.0), 1.0)

def run_pettitt_rolling_window(
    data: np.ndarray,
    window_size: int = 12,
    stride: int = 1,
    alpha: float = 0.01
) -> List[Dict]:
    """
    Run Pettitt's test on a rolling window over the data.
    
    Args:
        data: 1D numpy array of observations.
        window_size: Size of the rolling window.
        stride: Step size for the rolling window.
        alpha: Significance level for the test.
        
    Returns:
        List of dictionaries containing:
            - window_start: Index of the start of the window
            - window_end: Index of the end of the window (exclusive)
            - change_point: Index of the change point relative to the window start
            - absolute_change_point: Index of the change point in the original data
            - statistic: Pettitt statistic value
            - p_value: Approximate p-value
            - is_significant: Boolean indicating if p < alpha
    """
    results = []
    n = len(data)
    
    if window_size > n:
        logger.warning(f"Window size {window_size} larger than data length {n}. Skipping.")
        return results
    
    for start in range(0, n - window_size + 1, stride):
        end = start + window_size
        window_data = data[start:end]
        
        # Check for constant segments or NaNs (should be handled by preprocessing, but safe guard)
        if np.isnan(window_data).any():
            logger.warning(f"Skipping window {start}-{end} due to NaN values.")
            continue
        
        if np.std(window_data) == 0:
            # Constant segment, no change point possible
            logger.debug(f"Skipping window {start}-{end} due to zero variance.")
            continue
        
        # Compute Pettitt statistic
        cp_rel, stat = pettitt_statistic(window_data)
        
        # Compute p-value
        p_val = pettitt_p_value(stat, window_size)
        
        is_sig = p_val < alpha
        
        results.append({
            "window_start": start,
            "window_end": end,
            "change_point": cp_rel,
            "absolute_change_point": start + cp_rel,
            "statistic": stat,
            "p_value": p_val,
            "is_significant": is_sig
        })
        
    return results

def main():
    """
    Main entry point for running the Pettitt rolling-window test.
    Reads preprocessed data, runs the test, and saves results to baselines.csv.
    """
    setup_logging()
    
    # Load config
    config_path = "code/config.yaml"
    if not os.path.exists(config_path):
        logger.error(f"Config file not found: {config_path}")
        sys.exit(1)
        
    import yaml
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    window_size = config.get("window_size", 12)
    stride = config.get("stride", 1)
    alpha = config.get("alpha", 0.01)
    
    # Load preprocessed data
    processed_data_path = "data/processed/ili_processed.csv"
    if not os.path.exists(processed_data_path):
        logger.error(f"Processed data not found: {processed_data_path}. Run preprocess.py first.")
        sys.exit(1)
        
    df = pd.read_csv(processed_data_path)
    
    # Expect 'value' column (standardized ILI)
    if 'value' not in df.columns:
        logger.error("Processed data must contain a 'value' column.")
        sys.exit(1)
        
    data = df['value'].values
    weeks = df['week'].values if 'week' in df.columns else np.arange(len(data))
    
    logger.info(f"Running Pettitt rolling-window test on {len(data)} data points.")
    logger.info(f"Window size: {window_size}, Stride: {stride}, Alpha: {alpha}")
    
    results = run_pettitt_rolling_window(data, window_size, stride, alpha)
    
    if not results:
        logger.warning("No results generated from Pettitt test.")
        # Create an empty dataframe with correct columns
        output_df = pd.DataFrame(columns=[
            "window_start", "window_end", "change_point", 
            "absolute_change_point", "statistic", "p_value", "is_significant", "method"
        ])
    else:
        output_df = pd.DataFrame(results)
        output_df['method'] = 'pettitt'
        
        # Filter only significant changes for the final output? 
        # The task says "output baselines.csv containing detected change weeks".
        # We'll output all, but mark significance.
        # Usually, we only report significant ones as "detected".
        # Let's filter for significant ones to match the "detected change weeks" description.
        significant_df = output_df[output_df['is_significant']].copy()
        
        if significant_df.empty:
            logger.info("No significant change points detected by Pettitt test.")
            output_df = pd.DataFrame(columns=[
                "week", "statistic", "p_value", "method"
            ])
        else:
            # Prepare final output: just the detected change points
            # The column 'absolute_change_point' is the index in the original data.
            # We need to map this to the actual week value if available.
            # If 'week' column exists in df, we can map.
            if 'week' in df.columns:
                # Create a mapping from index to week
                idx_to_week = dict(zip(df.index, df['week']))
                significant_df['detected_week'] = significant_df['absolute_change_point'].map(idx_to_week)
                final_cols = ['detected_week', 'statistic', 'p_value', 'method']
            else:
                final_cols = ['absolute_change_point', 'statistic', 'p_value', 'method']
                significant_df.rename(columns={'absolute_change_point': 'detected_week'}, inplace=True)
                
            output_df = significant_df[final_cols]
    
    # Save to data/processed/baselines.csv (or data/processed/pettitt_results.csv)
    # The task description for T025 says "Output baselines.csv".
    # We'll save it to data/processed/baselines.csv to be consistent with T025.
    output_path = "data/processed/baselines.csv"
    output_df.to_csv(output_path, index=False)
    
    logger.info(f"Pettitt results saved to {output_path}")
    logger.info(f"Detected {len(output_df)} significant change points.")

if __name__ == "__main__":
    main()
