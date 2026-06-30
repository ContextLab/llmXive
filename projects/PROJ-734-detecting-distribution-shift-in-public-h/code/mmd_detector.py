import os
import sys
import logging
import time
import numpy as np
import pandas as pd
from typing import Tuple, List, Dict, Optional, Any

# Import from project modules as per API surface
from main import load_config
from preprocess import load_ili_data, remove_missing_weeks, log_transform, standardize
from exceptions import E_NO_DATA

logger = logging.getLogger(__name__)

def compute_gaussian_kernel(X: np.ndarray, Y: np.ndarray, sigma: float) -> np.ndarray:
    """
    Compute the Gaussian (RBF) kernel matrix between samples X and Y.
    K(x, y) = exp(-||x - y||^2 / (2 * sigma^2))
    """
    # Compute squared Euclidean distances
    # X: (n, d), Y: (m, d)
    # ||x - y||^2 = ||x||^2 + ||y||^2 - 2 * x.y
    XX = np.sum(X ** 2, axis=1).reshape(-1, 1)
    YY = np.sum(Y ** 2, axis=1).reshape(1, -1)
    dist_sq = XX + YY - 2 * np.dot(X, Y.T)
    dist_sq = np.maximum(dist_sq, 0.0) # Numerical stability

    return np.exp(-dist_sq / (2 * sigma ** 2))

def compute_mmd_statistic(X: np.ndarray, Y: np.ndarray, K: np.ndarray) -> float:
    """
    Compute the unbiased MMD statistic given kernel matrix K.
    K is the combined kernel matrix for [X; Y].
    Formula: (1/(n(n-1))) * sum_{i!=j} K(x_i, x_j)
           + (1/(m(m-1))) * sum_{i!=j} K(y_i, y_j)
           - (2/(nm)) * sum_{i,j} K(x_i, y_j)
    """
    n = X.shape[0]
    m = Y.shape[0]

    if n < 2 or m < 2:
        logger.warning("Sample size too small for unbiased MMD. Returning 0.")
        return 0.0

    # Split K into blocks
    K_xx = K[:n, :n]
    K_yy = K[n:, n:]
    K_xy = K[:n, n:]

    # Sum of off-diagonal elements for K_xx
    sum_xx = np.sum(K_xx) - np.trace(K_xx)
    term1 = sum_xx / (n * (n - 1))

    # Sum of off-diagonal elements for K_yy
    sum_yy = np.sum(K_yy) - np.trace(K_yy)
    term2 = sum_yy / (m * (m - 1))

    # Sum of all elements for K_xy
    sum_xy = np.sum(K_xy)
    term3 = (2.0 * sum_xy) / (n * m)

    mmd_sq = term1 + term2 - term3
    return mmd_sq

def estimate_bandwidth(X: np.ndarray, Y: np.ndarray) -> float:
    """
    Estimate the bandwidth (sigma) for the Gaussian kernel using the median heuristic.
    sigma = median(||x - y||) for x in X, y in Y
    """
    # Concatenate
    data = np.vstack([X, Y])
    n = X.shape[0]
    m = Y.shape[0]

    # Compute pairwise distances between X and Y
    XX = np.sum(X ** 2, axis=1).reshape(-1, 1)
    YY = np.sum(Y ** 2, axis=1).reshape(1, -1)
    dist_sq = XX + YY - 2 * np.dot(X, Y.T)
    dist_sq = np.maximum(dist_sq, 0.0)
    dist = np.sqrt(dist_sq)

    # Flatten and find median
    distances = dist.flatten()
    sigma = np.median(distances)
    
    if sigma == 0:
        sigma = 1.0 # Fallback to avoid division by zero
    
    return sigma

def compute_permutation_pvalue(
    mmd_obs: float, 
    K_combined: np.ndarray, 
    n: int, 
    m: int, 
    permutations: int, 
    seed: int = 42
) -> Tuple[float, int]:
    """
    Compute the p-value using a permutation test.
    Returns (p_value, time_elapsed).
    Implements runtime monitoring: if time > 30 mins, reduce permutations.
    """
    start_time = time.time()
    time_limit = 30 * 60 # 30 minutes in seconds
    
    current_permutations = permutations
    reduced = False
    
    np.random.seed(seed)
    
    # Pre-allocate array for permuted MMDs
    mmd_permuted = np.zeros(current_permutations)
    
    combined = np.vstack([np.zeros(n), np.ones(m)]) # Labels: 0 for X, 1 for Y
    total = n + m
    
    count = 0
    for i in range(current_permutations):
        elapsed = time.time() - start_time
        if elapsed > time_limit:
            if not reduced:
                logger.warning(f"Permutation test exceeded {time_limit}s. Halving permutations.")
                # Halve remaining permutations
                remaining = current_permutations - i
                new_remaining = max(1, remaining // 2)
                current_permutations = i + new_remaining
                # Truncate the array
                mmd_permuted = mmd_permuted[:current_permutations]
                reduced = True
                logger.warning(f"Reducing permutations to {current_permutations} to meet time limit.")
            else:
                break
        
        # Permute labels
        perm_indices = np.random.permutation(total)
        # Reconstruct X_perm and Y_perm based on permuted labels
        # We only need the kernel matrix, which is fixed.
        # We just need to re-calculate MMD for the new partition.
        
        # Efficient calculation using precomputed K_combined
        # K_combined is (total, total)
        # New X indices: perm_indices[:n], New Y indices: perm_indices[n:]
        
        idx_x = perm_indices[:n]
        idx_y = perm_indices[n:]
        
        K_xx = K_combined[np.ix_(idx_x, idx_x)]
        K_yy = K_combined[np.ix_(idx_y, idx_y)]
        K_xy = K_combined[np.ix_(idx_x, idx_y)]
        
        # Unbiased MMD calculation inline for speed
        sum_xx = np.sum(K_xx) - np.trace(K_xx)
        term1 = sum_xx / (n * (n - 1)) if n > 1 else 0.0
        
        sum_yy = np.sum(K_yy) - np.trace(K_yy)
        term2 = sum_yy / (m * (m - 1)) if m > 1 else 0.0
        
        sum_xy = np.sum(K_xy)
        term3 = (2.0 * sum_xy) / (n * m)
        
        mmd_sq = term1 + term2 - term3
        mmd_permuted[i] = mmd_sq
        count += 1

    actual_permutations = count
    
    # Calculate p-value
    # p = (1 + count(mmd_perm >= mmd_obs)) / (1 + permutations)
    # Using >= for one-sided test (MMD > 0 implies difference)
    # Standard convention: count how many permuted stats are >= observed
    count_ge = np.sum(mmd_permuted >= mmd_obs)
    p_value = (1.0 + count_ge) / (1.0 + actual_permutations)
    
    elapsed = time.time() - start_time
    return p_value, elapsed

def detect_shifts(
    df: pd.DataFrame, 
    window_size: int, 
    stride: int, 
    permutations: int, 
    alpha: float,
    seed: int = 42
) -> pd.DataFrame:
    """
    Detect distribution shifts using MMD with Bonferroni correction.
    
    Args:
        df: Preprocessed DataFrame with 'week' and 'value' columns.
        window_size: Number of weeks in each window.
        stride: Step size between windows.
        permutations: Number of permutations for p-value estimation.
        alpha: Base significance level (e.g., 0.01).
        seed: Random seed for reproducibility.
    
    Returns:
        DataFrame with columns: week_start, week_end, mmd_stat, p_value, is_shifted
    """
    if len(df) < window_size * 2:
        logger.warning("Data too short for two windows of size {window_size}.")
        return pd.DataFrame(columns=['week_start', 'week_end', 'mmd_stat', 'p_value', 'is_shifted'])

    # Extract values
    values = df['value'].values
    weeks = df['week'].values

    # Generate windows
    windows = []
    for i in range(0, len(values) - window_size, stride):
        if i + window_size * 2 > len(values):
            break
        windows.append((i, i + window_size))

    if len(windows) < 2:
        logger.warning("Not enough windows to compare.")
        return pd.DataFrame(columns=['week_start', 'week_end', 'mmd_stat', 'p_value', 'is_shifted'])

    results = []
    
    # Calculate N: number of window pairs (comparisons)
    # We compare window i with window i+1 (sliding pairs)
    # Or all pairs? The task says "number of window pairs".
    # Standard approach for time series: compare adjacent windows (i, i+1)
    # Let's assume adjacent pairs for this implementation.
    N = len(windows) - 1
    
    if N == 0:
        logger.warning("Only one window available, no pairs to compare.")
        return pd.DataFrame(columns=['week_start', 'week_end', 'mmd_stat', 'p_value', 'is_shifted'])

    # Bonferroni correction
    bonferroni_alpha = alpha / N
    logger.info(f"Total window pairs (N): {N}. Bonferroni corrected alpha: {bonferroni_alpha:.6f}")

    for i in range(N):
        idx_start_1, idx_end_1 = windows[i]
        idx_start_2, idx_end_2 = windows[i+1]
        
        X = values[idx_start_1:idx_end_1]
        Y = values[idx_start_2:idx_end_2]
        
        # Ensure 2D for kernel function
        X = X.reshape(-1, 1)
        Y = Y.reshape(-1, 1)
        
        # Estimate bandwidth
        sigma = estimate_bandwidth(X, Y)
        
        # Compute combined kernel matrix
        # Combined data: [X; Y]
        combined_data = np.vstack([X, Y])
        K_combined = compute_gaussian_kernel(combined_data, combined_data, sigma)
        
        # Compute observed MMD
        mmd_obs = compute_mmd_statistic(X, Y, K_combined)
        
        # Compute p-value
        p_val, elapsed = compute_permutation_pvalue(
            mmd_obs, K_combined, X.shape[0], Y.shape[0], permutations, seed
        )
        
        is_shifted = p_val < bonferroni_alpha
        
        results.append({
            'week_start': weeks[idx_start_1],
            'week_end': weeks[idx_end_2], # End of the second window
            'mmd_stat': mmd_obs,
            'p_value': p_val,
            'is_shifted': is_shifted,
            'bonferroni_threshold': bonferroni_alpha
        })
        
        logger.debug(f"Window pair {i}: p={p_val:.4f}, threshold={bonferroni_alpha:.6f}, shifted={is_shifted}")

    return pd.DataFrame(results)

def main():
    """
    Main entry point for the MMD detector pipeline.
    Loads config, preprocesses data, runs detection, and saves flags.csv.
    """
    setup_logger = logging.getLogger(__name__)
    if not setup_logger.handlers:
        # Basic setup if not already done
        logging.basicConfig(level=logging.INFO)
    
    logger.info("Starting MMD Shift Detection Pipeline")
    
    try:
        config = load_config()
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        sys.exit(1)

    try:
        # Load and preprocess data
        df_raw = load_ili_data()
        df_clean = remove_missing_weeks(df_raw)
        df_log = log_transform(df_clean)
        df_std = standardize(df_log)
        
        logger.info(f"Preprocessed data shape: {df_std.shape}")
    except E_NO_DATA:
        logger.error("Data availability check failed. Exiting.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        sys.exit(1)

    # Run detection
    try:
        flags_df = detect_shifts(
            df_std,
            window_size=config.window_size,
            stride=config.stride,
            permutations=config.permutations,
            alpha=config.alpha,
            seed=config.seed
        )
    except Exception as e:
        logger.error(f"Detection failed: {e}")
        sys.exit(1)

    if flags_df.empty:
        logger.warning("No shifts detected or no data to process.")
    else:
        # Save flags.csv
        output_path = "data/processed/flags.csv"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        flags_df.to_csv(output_path, index=False)
        logger.info(f"Flags saved to {output_path}")
        
        # Log summary
        shifted_count = flags_df['is_shifted'].sum()
        logger.info(f"Total comparisons: {len(flags_df)}, Shifts detected: {shifted_count}")

    return flags_df

if __name__ == "__main__":
    main()