import numpy as np
from scipy import signal
from typing import Union, Optional
import pandas as pd
from code import logger
from code.config import STREAMING_CHUNK_SIZE

def calculate_effective_sample_size_neff(series: pd.Series) -> float:
    """
    Calculate the effective sample size (Neff) using the Pyper & Peterman formula.
    
    This function:
    1. Detrends the series to remove linear trends.
    2. Calculates the lag-1 autocorrelation of the residuals.
    3. Applies the formula: Neff = N * (1 - rho_1) / (1 + rho_1)
    
    Args:
        series (pd.Series): The input time series data.
        
    Returns:
        float: The effective sample size.
        
    Raises:
        ValueError: If the series is too short to calculate autocorrelation.
    """
    if len(series) < 5:
        raise ValueError(f"Series too short ({len(series)} points) to calculate autocorrelation. Minimum 5 points required.")
    
    # Convert to numpy array for scipy operations
    data = series.values.astype(float)
    
    # Remove NaNs if any (though aligned data should be clean)
    mask = ~np.isnan(data)
    if not np.all(mask):
        logger.warning(f"Detected {np.sum(~mask)} NaNs in series, dropping them for Neff calculation.")
        data = data[mask]
    
    if len(data) < 5:
        raise ValueError(f"Series too short after NaN removal ({len(data)} points). Minimum 5 points required.")
        
    # Detrend the series using scipy.signal.detrend (removes linear trend)
    residuals = signal.detrend(data)
    
    # Calculate lag-1 autocorrelation of the residuals
    # rho_1 = Cov(X_t, X_{t-1}) / Var(X_t)
    # We compute this manually to ensure we use the residuals specifically
    n = len(residuals)
    mean_res = np.mean(residuals)
    
    # Variance of residuals
    var_res = np.sum((residuals - mean_res) ** 2)
    if var_res == 0:
        # If variance is 0, the series is constant, Neff = N
        logger.warning("Series has zero variance after detrending. Returning N as Neff.")
        return float(n)
    
    # Covariance at lag 1
    # Cov(X_t, X_{t-1}) = sum((x_t - mean)(x_{t-1} - mean)) / n
    # Note: Standard autocorrelation often uses n-1 or n-2 in denominator, 
    # but for the Pyper & Peterman formula, we need the correlation coefficient.
    # corr = cov / var
    lag1_product = np.sum((residuals[1:] - mean_res) * (residuals[:-1] - mean_res))
    
    # Calculate rho_1
    # We use the same denominator logic for consistency: sum((x-mean)^2)
    # rho_1 = sum((x_t - mean)(x_{t-1} - mean)) / sum((x_t - mean)^2)
    # Note: The denominator sum is over n-1 terms if we align indices 1..n and 0..n-1
    # However, for large n, the difference is negligible.
    # To be precise with the correlation coefficient definition:
    # r = sum((x_i - x_mean)(y_i - y_mean)) / sqrt(sum(x_diff^2) * sum(y_diff^2))
    # Here x and y are the same series shifted.
    
    # Let's use the standard definition for lag-1 autocorrelation coefficient
    # rho_1 = sum_{t=2}^N (x_t - x_bar)(x_{t-1} - x_bar) / sum_{t=1}^N (x_t - x_bar)^2
    # Using the full variance sum in denominator is common in this context.
    
    rho_1 = lag1_product / var_res
    
    # Clamp rho_1 to [-1, 1] to avoid numerical errors causing division by zero or negative Neff
    rho_1 = np.clip(rho_1, -1.0, 1.0)
    
    # Apply Pyper & Peterman formula
    # Neff = N * (1 - rho_1) / (1 + rho_1)
    # Handle edge case where rho_1 is close to 1
    if abs(1 + rho_1) < 1e-9:
        logger.warning("Lag-1 autocorrelation is close to 1. Neff may be very small or unstable.")
        neff = 1.0 # Minimum effective sample size
    else:
        neff = n * (1 - rho_1) / (1 + rho_1)
    
    # Ensure Neff is at least 1
    neff = max(1.0, neff)
    
    logger.info(f"Neff calculated: N={n}, rho_1={rho_1:.4f}, Neff={neff:.2f}")
    return float(neff)

def calculate_neff(series: Union[pd.Series, np.ndarray]) -> float:
    """
    Wrapper for calculate_effective_sample_size_neff to maintain API compatibility.
    
    Args:
        series: Input time series.
        
    Returns:
        float: Effective sample size.
    """
    if isinstance(series, np.ndarray):
        series = pd.Series(series)
    return calculate_effective_sample_size_neff(series)

def calculate_neff_chunked(filepath: str, chunksize: int = STREAMING_CHUNK_SIZE) -> float:
    """
    Calculate Neff for a large dataset by processing in chunks.
    
    This function reads the data in chunks, accumulates the necessary statistics
    to compute the global lag-1 autocorrelation, and then applies the Neff formula.
    
    Note: For accurate global Neff on a continuous time series, we need the 
    autocorrelation of the entire series, not the average of chunk autocorrelations.
    This implementation calculates the lag-1 autocorrelation across chunk boundaries
    as well.
    
    Args:
        filepath: Path to the CSV file containing the time series.
        chunksize: Number of rows per chunk.
        
    Returns:
        float: Effective sample size for the full series.
    """
    logger.info(f"Calculating Neff in chunks for file: {filepath}")
    
    # We need to calculate the global lag-1 autocorrelation.
    # rho_1 = sum((x_t - mean)(x_{t-1} - mean)) / sum((x_t - mean)^2)
    # We can accumulate:
    # 1. Sum of x
    # 2. Sum of x^2
    # 3. Sum of x_t * x_{t-1} (requires tracking the last value of the previous chunk)
    # 4. Count of valid pairs
    
    # However, detrending first is required. Detrending requires the global mean and slope.
    # Calculating global trend on a stream is possible but complex.
    # Alternative: Calculate global mean first, then detrend in chunks.
    
    # Step 1: Calculate global mean
    global_sum = 0.0
    global_count = 0
    total_sum_sq = 0.0 # For variance calculation later if needed, but we need sum(x^2) for detrend slope?
    
    # First pass: get global mean
    # We assume the column of interest is the first numeric column or named 'value'
    # For this implementation, we assume the file has a 'timestamp' and one value column.
    # Or we iterate over all numeric columns if needed. Let's assume a single series for now.
    # If the file has multiple columns, we need to know which one.
    # Given the context, we'll assume the data is aligned and we are calculating for a specific series.
    # To be robust, we'll read the first chunk to determine the numeric column.
    
    first_chunk = pd.read_csv(filepath, chunksize=chunksize)
    chunk_df = next(first_chunk)
    numeric_cols = chunk_df.select_dtypes(include=[np.number]).columns
    
    if len(numeric_cols) == 0:
        raise ValueError("No numeric columns found in the file.")
    
    # Assume the first numeric column is the one we want, or if 'value' exists, use it.
    target_col = 'value' if 'value' in numeric_cols else numeric_cols[0]
    logger.info(f"Using column '{target_col}' for Neff calculation.")
    
    # Reset iterator
    del first_chunk
    
    # Pass 1: Calculate global mean
    total_sum = 0.0
    total_count = 0
    
    for chunk in pd.read_csv(filepath, usecols=[target_col], chunksize=chunksize):
        vals = chunk[target_col].dropna().values
        total_sum += np.sum(vals)
        total_count += len(vals)
        
    if total_count == 0:
        raise ValueError("No valid data points found.")
        
    global_mean = total_sum / total_count
    logger.info(f"Global mean calculated: {global_mean}")
    
    # Pass 2: Calculate detrended series statistics for lag-1 autocorrelation
    # We need sum((x_t - mean)^2) and sum((x_t - mean)(x_{t-1} - mean))
    # Since we are detrending with a constant (mean) for now (simple detrend),
    # we can compute these directly.
    # Note: scipy.signal.detrend(type='linear') removes a linear trend.
    # For a simple mean removal, it's 'constant'.
    # The task says "detrending with scipy.signal.detrend" which defaults to linear.
    # Calculating a global linear trend on a stream requires:
    # sum(x), sum(t), sum(t^2), sum(x*t).
    # Let's implement the linear detrend accumulation.
    
    sum_x = 0.0
    sum_t = 0.0
    sum_t2 = 0.0
    sum_xt = 0.0
    n_points = 0
    
    # We need to track the absolute index t for the linear trend
    current_idx = 0
    
    # First, accumulate for linear trend calculation
    for chunk in pd.read_csv(filepath, usecols=[target_col], chunksize=chunksize):
        vals = chunk[target_col].dropna().values
        n = len(vals)
        if n == 0:
            continue
            
        # Indices for this chunk: current_idx to current_idx + n - 1
        # We can compute sum(t), sum(t^2), sum(x), sum(xt) for this chunk
        indices = np.arange(current_idx, current_idx + n)
        
        sum_x += np.sum(vals)
        sum_t += np.sum(indices)
        sum_t2 += np.sum(indices**2)
        sum_xt += np.sum(vals * indices)
        
        n_points += n
        current_idx += n
        
    if n_points < 2:
        raise ValueError("Not enough points to calculate linear trend.")
        
    # Calculate slope and intercept for linear trend: y = a + b*t
    # b = (n*sum(xt) - sum(x)*sum(t)) / (n*sum(t2) - sum(t)^2)
    # a = (sum(x) - b*sum(t)) / n
    
    denom = n_points * sum_t2 - sum_t**2
    if abs(denom) < 1e-12:
        logger.warning("Denominator for linear trend is near zero. Using mean detrend.")
        slope = 0.0
        intercept = global_mean
    else:
        slope = (n_points * sum_xt - sum_x * sum_t) / denom
        intercept = (sum_x - slope * sum_t) / n_points
        
    logger.info(f"Linear trend: intercept={intercept}, slope={slope}")
    
    # Now, calculate the residuals and lag-1 autocorrelation
    # We need sum(resid^2) and sum(resid_t * resid_{t-1})
    # resid_t = x_t - (intercept + slope * t)
    
    sum_resid_sq = 0.0
    sum_resid_prod = 0.0
    total_valid_pairs = 0
    
    prev_resid = None
    prev_t = -1
    
    for chunk in pd.read_csv(filepath, usecols=[target_col], chunksize=chunksize):
        vals = chunk[target_col].dropna().values
        n = len(vals)
        if n == 0:
            continue
            
        indices = np.arange(current_idx - n, current_idx) # Current chunk indices
        
        # Calculate residuals for this chunk
        trend_vals = intercept + slope * indices
        residuals = vals - trend_vals
        
        # Accumulate sum of squared residuals
        sum_resid_sq += np.sum(residuals**2)
        
        # Calculate sum of products for lag-1
        # We need to connect the last residual of the previous chunk with the first of this chunk
        
        # Internal chunk pairs
        if n > 1:
            internal_prod = np.sum(residuals[1:] * residuals[:-1])
            sum_resid_prod += internal_prod
            total_valid_pairs += n - 1
            
        # Cross-chunk pair
        if prev_resid is not None:
            # Pair: (prev_resid, current_first_resid)
            sum_resid_prod += prev_resid * residuals[0]
            total_valid_pairs += 1
            
        # Update previous
        prev_resid = residuals[-1]
        prev_t = indices[-1]
        
        current_idx -= n # This logic is wrong for the loop, let's fix the index tracking
        # Actually, current_idx was incremented in the first pass.
        # We need to re-track or just use a separate counter.
        # Let's just use a simple counter for the second pass.
        
    # Re-implementing the second pass with correct index tracking
    # Reset for second pass
    current_idx = 0
    sum_resid_sq = 0.0
    sum_resid_prod = 0.0
    total_valid_pairs = 0
    prev_resid = None
    
    for chunk in pd.read_csv(filepath, usecols=[target_col], chunksize=chunksize):
        vals = chunk[target_col].dropna().values
        n = len(vals)
        if n == 0:
            continue
            
        indices = np.arange(current_idx, current_idx + n)
        trend_vals = intercept + slope * indices
        residuals = vals - trend_vals
        
        sum_resid_sq += np.sum(residuals**2)
        
        if n > 1:
            sum_resid_prod += np.sum(residuals[1:] * residuals[:-1])
            total_valid_pairs += n - 1
            
        if prev_resid is not None:
            sum_resid_prod += prev_resid * residuals[0]
            total_valid_pairs += 1
            
        prev_resid = residuals[-1]
        current_idx += n
        
    if sum_resid_sq == 0:
        logger.warning("Residuals have zero variance. Returning N as Neff.")
        return float(n_points)
        
    rho_1 = sum_resid_prod / sum_resid_sq
    rho_1 = np.clip(rho_1, -1.0, 1.0)
    
    if abs(1 + rho_1) < 1e-9:
        neff = 1.0
    else:
        neff = n_points * (1 - rho_1) / (1 + rho_1)
        
    neff = max(1.0, neff)
    logger.info(f"Chunked Neff calculated: N={n_points}, rho_1={rho_1:.4f}, Neff={neff:.2f}")
    return float(neff)