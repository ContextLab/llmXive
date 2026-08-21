import numpy as np
import pandas as pd
from scipy import signal
from scipy.stats import linregress
from typing import Dict, Any, Union, List, Optional
import logging

class MetricsError(Exception):
    """Custom exception for metrics calculation errors."""
    pass

def compute_acf_lag(series: np.ndarray, max_lag: int = 20) -> List[float]:
    """
    Compute Autocorrelation Function (ACF) for lags 0 to max_lag.
    
    Args:
        series: Input time series (numpy array)
        max_lag: Maximum lag to compute (default 20)
        
    Returns:
        List of ACF values for lags 0 to max_lag
    """
    if len(series) < max_lag + 1:
        raise MetricsError(f"Series length {len(series)} is too short for max_lag {max_lag}")
    
    acf_values = []
    n = len(series)
    mean = np.mean(series)
    var = np.var(series)
    
    if var == 0:
        # If variance is zero, ACF is undefined (or 0 for lags > 0)
        return [1.0] + [0.0] * max_lag
    
    for lag in range(max_lag + 1):
        if lag == 0:
            acf_values.append(1.0)
        else:
            # Compute autocorrelation at specific lag
            cov = np.mean((series[:n-lag] - mean) * (series[lag:] - mean))
            acf_values.append(cov / var)
    
    return acf_values

def compute_dfa_hurst(series: np.ndarray) -> float:
    """
    Compute Hurst exponent using Detrended Fluctuation Analysis (DFA).
    
    Note: Per FR-002, DFA is excluded from the preprocessing pipeline,
    but this function is provided for reference/alternative analysis.
    
    Args:
        series: Input time series (numpy array)
        
    Returns:
        Estimated Hurst exponent
    """
    if len(series) < 10:
        raise MetricsError("Series too short for DFA")
    
    # Integrate series (profile)
    profile = np.cumsum(series - np.mean(series))
    n = len(profile)
    
    # Define window sizes
    min_n = 4
    max_n = n // 4
    if max_n < min_n:
        max_n = min_n
        
    scales = np.logspace(np.log10(min_n), np.log10(max_n), num=10, dtype=int)
    
    fluctuation = []
    for scale in scales:
        # Divide into non-overlapping segments
        num_segments = n // scale
        if num_segments == 0:
            continue
            
        rms_sum = 0
        for seg_idx in range(num_segments):
            start = seg_idx * scale
            end = start + scale
            segment = profile[start:end]
            
            # Fit linear trend
            x = np.arange(scale)
            slope, intercept, _, _, _ = linregress(x, segment)
            trend = slope * x + intercept
            
            # Detrend
            detrended = segment - trend
            rms_sum += np.sqrt(np.mean(detrended ** 2))
        
        rms = np.sqrt(rms_sum / num_segments)
        fluctuation.append(rms)
    
    if len(fluctuation) < 2:
        raise MetricsError("Not enough scales for DFA")
    
    # Fit log-log relationship
    log_scales = np.log(scales[:len(fluctuation)])
    log_fluctuation = np.log(fluctuation)
    
    slope, _, _, _, _ = linregress(log_scales, log_fluctuation)
    return float(slope)

def compute_spectral_peak_ratio(series: np.ndarray) -> float:
    """
    Compute spectral density peak ratio.
    
    Algorithm:
    1. Compute power spectral density (PSD) using Welch's method
    2. Identify low-frequency band (0 to 0.1 * Nyquist)
    3. Identify high-frequency band (0.4 * Nyquist to 0.5 * Nyquist)
    4. Peak ratio = (max peak in low-freq band) / (mean floor in high-freq band)
    
    Args:
        series: Input time series (numpy array)
        
    Returns:
        Spectral peak ratio
        
    Raises:
        MetricsError: If numerical instability occurs or series is too short
    """
    if len(series) < 64:
        raise MetricsError(f"Series length {len(series)} is too short for spectral analysis")
    
    try:
        # Compute PSD using Welch's method
        fs = 1.0  # Normalize to unit sampling frequency
        nperseg = min(256, len(series))
        f, psd = signal.welch(series, fs=fs, nperseg=nperseg, scaling='density')
        
        # Define frequency bands
        nyquist = fs / 2
        low_freq_max = 0.1 * nyquist
        high_freq_min = 0.4 * nyquist
        high_freq_max = 0.5 * nyquist
        
        # Extract low-frequency band
        low_mask = (f >= 0) & (f <= low_freq_max)
        low_psd = psd[low_mask]
        
        # Extract high-frequency band
        high_mask = (f >= high_freq_min) & (f <= high_freq_max)
        high_psd = psd[high_mask]
        
        if len(low_psd) == 0 or len(high_psd) == 0:
            raise MetricsError("Frequency bands are empty")
        
        # Calculate metrics
        max_peak = np.max(low_psd)
        mean_floor = np.mean(high_psd)
        
        # Handle numerical instability
        if mean_floor <= 0:
            raise MetricsError("Mean floor in high-freq band is non-positive")
        
        ratio = max_peak / mean_floor
        
        if not np.isfinite(ratio):
            raise MetricsError("Spectral peak ratio is not finite")
        
        return float(ratio)
        
    except Exception as e:
        raise MetricsError(f"Spectral density calculation failed: {str(e)}")

def compute_all_metrics(series: np.ndarray) -> Dict[str, Any]:
    """
    Compute all metrics for a time series: ACF, Hurst, and Spectral Peak Ratio.
    
    Args:
        series: Input time series (numpy array)
        
    Returns:
        Dictionary containing:
            - acf_vector: List of ACF values (lags 0-20)
            - hurst: Hurst exponent estimate
            - spectral_peak_ratio: Spectral density peak ratio
            - variance_fallback: Variance of series (computed regardless of other failures)
    """
    result = {
        'acf_vector': [],
        'hurst': None,
        'spectral_peak_ratio': None,
        'variance_fallback': float(np.var(series))
    }
    
    # Compute ACF
    try:
        result['acf_vector'] = compute_acf_lag(series, max_lag=20)
    except MetricsError as e:
        logging.warning(f"ACF calculation failed: {e}")
        result['acf_vector'] = [0.0] * 21
    
    # Compute Hurst
    try:
        result['hurst'] = compute_dfa_hurst(series)
    except MetricsError as e:
        logging.warning(f"Hurst calculation failed: {e}")
    
    # Compute Spectral Peak Ratio
    try:
        result['spectral_peak_ratio'] = compute_spectral_peak_ratio(series)
    except MetricsError as e:
        logging.warning(f"Spectral peak ratio failed: {e}")
        # Per T051: explicitly calculate variance as fallback and store it
        # The variance is already stored in 'variance_fallback', but we ensure it's set here
        result['variance_fallback'] = float(np.var(series))
    
    return result

def compute_metrics_for_dataset(series: Union[np.ndarray, pd.Series], source: str) -> Dict[str, Any]:
    """
    Compute metrics for a dataset with source identification.
    
    Args:
        series: Input time series (numpy array or pandas Series)
        source: Source identifier for the dataset
        
    Returns:
        Dictionary containing source, length, and all computed metrics
    """
    if isinstance(series, pd.Series):
        series = series.values
    
    metrics = compute_all_metrics(series)
    
    return {
        'source': source,
        'length': len(series),
        'hurst': metrics['hurst'],
        'acf_vector': metrics['acf_vector'],
        'spectral_peak_ratio': metrics['spectral_peak_ratio'],
        'variance_fallback': metrics['variance_fallback']
    }
