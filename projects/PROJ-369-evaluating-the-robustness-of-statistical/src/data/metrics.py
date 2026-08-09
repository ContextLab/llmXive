"""
Metrics computation utilities for time series analysis.

Implements ACF, Hurst exponent (via DFA), and Spectral Density peak ratio.
"""
import numpy as np
import pandas as pd
from scipy import signal
from scipy.stats import linregress
from typing import Dict, Any, Union, List, Optional
import logging

# Configure logger for this module
logger = logging.getLogger(__name__)

class MetricsError(Exception):
    """Custom exception for metrics computation errors."""
    pass

def compute_acf_lag(series: Union[np.ndarray, pd.Series], max_lag: int = 10) -> Dict[int, float]:
    """
    Compute Autocorrelation Function (ACF) up to a specified lag.
    
    Args:
        series: Input time series (numpy array or pandas Series).
        max_lag: Maximum lag to compute.
        
    Returns:
        Dictionary mapping lag (int) to ACF value (float).
        
    Raises:
        MetricsError: If series is too short or computation fails.
    """
    if len(series) < max_lag + 10:
        raise MetricsError(f"Series length {len(series)} is too short for max_lag {max_lag}.")
    
    try:
        # Use pandas built-in for robustness, or scipy if needed
        # Using numpy implementation for clarity and control
        n = len(series)
        series_centered = series - np.mean(series)
        acf_values = {}
        
        for lag in range(max_lag + 1):
            if lag == 0:
                acf_values[lag] = 1.0
            else:
                # Compute autocorrelation at specific lag
                numerator = np.sum(series_centered[:-lag] * series_centered[lag:])
                denominator = np.sum(series_centered * series_centered)
                if denominator == 0:
                    acf_values[lag] = 0.0
                else:
                    acf_values[lag] = numerator / denominator
        
        return acf_values
    except Exception as e:
        logger.error(f"ACF computation failed: {e}")
        raise MetricsError(f"ACF computation failed: {e}")

def compute_dfa_hurst(series: Union[np.ndarray, pd.Series], min_scale: int = 4, max_scale: Optional[int] = None) -> float:
    """
    Compute Hurst exponent using Detrended Fluctuation Analysis (DFA).
    
    Note: While the spec mandates linear regression residuals for detrending
    in preprocessing, DFA is a valid method for estimating the Hurst exponent
    itself as a metric.
    
    Args:
        series: Input time series.
        min_scale: Minimum window size for DFA.
        max_scale: Maximum window size for DFA.
        
    Returns:
        Estimated Hurst exponent (float).
        
    Raises:
        MetricsError: If computation fails or series is too short.
    """
    if len(series) < min_scale * 2:
        raise MetricsError(f"Series length {len(series)} is too short for DFA.")
    
    if max_scale is None:
        max_scale = len(series) // 4
        if max_scale < min_scale:
            raise MetricsError("Series too short to determine valid scale range.")

    try:
        y = np.cumsum(series - np.mean(series))
        n = len(y)
        
        scales = []
        fluctuations = []
        
        # Define scales (window sizes)
        # Use a logarithmic spacing of scales
        n_scales = 10
        scales_list = np.logspace(np.log10(min_scale), np.log10(max_scale), n_scales).astype(int)
        scales_list = np.unique(scales_list)
        
        for scale in scales_list:
            if scale >= n:
                continue
            
            # Divide into non-overlapping segments
            num_segments = int(n / scale)
            fluctuation_sum = 0.0
            
            for seg_idx in range(num_segments):
                start = seg_idx * scale
                end = start + scale
                segment = y[start:end]
                
                # Fit a linear trend (local detrending)
                x_local = np.arange(scale)
                coeffs = np.polyfit(x_local, segment, 1)
                trend = np.polyval(coeffs, x_local)
                
                # Detrended series
                detrended = segment - trend
                fluctuation = np.sqrt(np.mean(detrended ** 2))
                fluctuation_sum += fluctuation ** 2
            
            if num_segments > 0:
                F = np.sqrt(fluctuation_sum / num_segments)
                scales.append(scale)
                fluctuations.append(F)
        
        if len(scales) < 2:
            raise MetricsError("Not enough valid scales for DFA regression.")
        
        # Linear regression in log-log space
        log_scales = np.log(scales)
        log_fluctuations = np.log(fluctuations)
        
        slope, _, _, _, _ = linregress(log_scales, log_fluctuations)
        
        return float(slope)
        
    except Exception as e:
        logger.error(f"DFA Hurst computation failed: {e}")
        raise MetricsError(f"DFA Hurst computation failed: {e}")

def compute_spectral_peak_ratio(series: Union[np.ndarray, pd.Series]) -> float:
    """
    Compute the spectral density peak ratio.
    
    This metric compares the maximum spectral density to the median (or mean)
    spectral density to quantify the "peakiness" of the spectrum, indicating
    periodicity or strong low-frequency components.
    
    Args:
        series: Input time series.
        
    Returns:
        Ratio of max spectral density to median spectral density.
        
    Raises:
        MetricsError: If computation fails.
    """
    if len(series) < 10:
        raise MetricsError("Series too short for spectral analysis.")
    
    try:
        # Compute power spectral density using Welch's method
        # fs=1.0 implies unit sampling interval
        f, Pxx = signal.welch(
            series - np.mean(series), 
            fs=1.0, 
            nperseg=min(256, len(series)),
            scaling='density'
        )
        
        if len(Pxx) == 0:
            raise MetricsError("Spectral density calculation returned empty array.")
        
        # Remove DC component (frequency 0) if present
        if f[0] == 0:
            Pxx = Pxx[1:]
            f = f[1:]
        
        if len(Pxx) == 0:
            raise MetricsError("No valid frequency bins after removing DC.")
        
        max_psd = np.max(Pxx)
        median_psd = np.median(Pxx)
        
        if median_psd == 0:
            # Fallback to mean if median is zero (unlikely but possible)
            median_psd = np.mean(Pxx)
        
        if median_psd == 0:
            return float('inf')
        
        return float(max_psd / median_psd)
        
    except Exception as e:
        logger.error(f"Spectral peak ratio computation failed: {e}")
        raise MetricsError(f"Spectral peak ratio computation failed: {e}")

def compute_all_metrics(series: Union[np.ndarray, pd.Series]) -> Dict[str, Any]:
    """
    Compute all metrics (ACF, Hurst, Spectral Peak Ratio) for a single series.
    
    Args:
        series: Input time series.
        
    Returns:
        Dictionary containing all computed metrics.
    """
    metrics = {}
    
    # ACF (Lag 1 to 10)
    try:
        acf_result = compute_acf_lag(series, max_lag=10)
        metrics['acf'] = acf_result
        metrics['acf_lag_1'] = acf_result.get(1, 0.0)
    except MetricsError as e:
        logger.warning(f"ACF skipped: {e}")
        metrics['acf'] = {}
        metrics['acf_lag_1'] = None
    
    # Hurst (DFA)
    try:
        metrics['hurst'] = compute_dfa_hurst(series)
    except MetricsError as e:
        logger.warning(f"Hurst skipped: {e}")
        metrics['hurst'] = None
    
    # Spectral Peak Ratio
    try:
        metrics['spectral_peak_ratio'] = compute_spectral_peak_ratio(series)
    except MetricsError as e:
        logger.warning(f"Spectral peak ratio skipped: {e}")
        metrics['spectral_peak_ratio'] = None
    
    return metrics

def compute_metrics_for_dataset(dataset: pd.DataFrame, value_column: str = 'value', date_column: str = 'datetime') -> Dict[str, Any]:
    """
    Compute metrics for a dataset (DataFrame).
    
    Args:
        dataset: DataFrame containing time series data.
        value_column: Name of the column containing the time series values.
        date_column: Name of the column containing timestamps (optional, used for sorting).
        
    Returns:
        Dictionary containing dataset info and computed metrics.
    """
    if value_column not in dataset.columns:
        raise MetricsError(f"Value column '{value_column}' not found in dataset.")
    
    series = dataset[value_column].dropna()
    
    if len(series) < 20:
        raise MetricsError(f"Series too short after dropping NaNs: {len(series)}")
    
    # Ensure sorted by date if date_column exists
    if date_column in dataset.columns:
        series = series.sort_index()
    
    metrics = compute_all_metrics(series.values)
    
    return {
        'n_points': len(series),
        'metrics': metrics
    }
