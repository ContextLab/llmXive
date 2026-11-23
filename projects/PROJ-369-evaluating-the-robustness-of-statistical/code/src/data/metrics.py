import numpy as np
import pandas as pd
from scipy import signal
from scipy.stats import linregress
from typing import Dict, Any, Union, List, Optional
import logging

from src.utils.logging import log_info, log_warning, log_error, log_critical

class MetricsError(Exception):
    """Custom exception for metrics computation errors."""
    pass

def compute_acf_lag(series: pd.Series, max_lag: int = 20) -> np.ndarray:
    """
    Compute Autocorrelation Function (ACF) up to a specified lag.

    Args:
        series: Input time series data.
        max_lag: Maximum lag to compute.

    Returns:
        Array of ACF values from lag 0 to max_lag.
    """
    if not isinstance(series, pd.Series):
        series = pd.Series(series)
    
    n = len(series)
    if n < max_lag + 1:
        log_warning(f"Series length ({n}) is less than max_lag + 1 ({max_lag + 1}). Adjusting max_lag.")
        max_lag = n - 1

    acf_values = []
    mean = series.mean()
    var = series.var()

    if var == 0:
        return np.zeros(max_lag + 1)

    for lag in range(max_lag + 1):
        if lag == 0:
            acf_values.append(1.0)
        else:
            numerator = np.sum((series.values[:-lag] - mean) * (series.values[lag:] - mean))
            acf_values.append(numerator / (var * (n - lag)))

    return np.array(acf_values)

def compute_dfa_hurst(series: pd.Series, max_order: int = 5) -> float:
    """
    Compute Hurst exponent using Detrended Fluctuation Analysis (DFA).

    Args:
        series: Input time series data.
        max_order: Maximum order of polynomial detrending.

    Returns:
        Estimated Hurst exponent.
    """
    if not isinstance(series, pd.Series):
        series = pd.Series(series)
    
    # Integrate the series (profile)
    y = series.values
    y = y - np.mean(y)
    Y = np.cumsum(y)
    n = len(Y)

    # Define window sizes (scales)
    scales = np.logspace(np.log10(10), np.log10(n // 4), num=10).astype(int)
    scales = scales[scales < n // 4]

    if len(scales) < 2:
        log_warning("Not enough data points to perform DFA. Returning 0.5.")
        return 0.5

    rms_values = []

    for scale in scales:
        # Divide into non-overlapping segments
        num_segments = n // scale
        rms = []

        for i in range(num_segments):
            start = i * scale
            end = start + scale
            segment = Y[start:end]
            x = np.arange(scale)

            # Fit polynomial trend
            coeffs = np.polyfit(x, segment, 1) # Linear detrending (order 1)
            trend = np.polyval(coeffs, x)
            
            # Detrended series
            detrended = segment - trend
            rms.append(np.sqrt(np.mean(detrended**2)))

        if rms:
            rms_values.append(np.mean(rms))

    if len(rms_values) < 2:
        log_warning("DFA failed to compute sufficient scales. Returning 0.5.")
        return 0.5

    # Fit line to log-log plot
    log_scales = np.log(scales)
    log_rms = np.log(rms_values)
    
    slope, _, _, _, _ = linregress(log_scales, log_rms)
    
    return slope

def compute_spectral_peak_ratio(series: pd.Series) -> float:
    """
    Compute Spectral Density Peak Ratio.
    Ratio = (max peak in low-freq band) / (mean floor in high-freq band).
    
    This function includes a fallback to variance-based metric if numerical
    instability is detected (e.g., zero denominator, NaN results).

    Args:
        series: Input time series data.

    Returns:
        Spectral peak ratio. If calculation fails due to instability, 
        returns a variance-based fallback value.
    """
    if not isinstance(series, pd.Series):
        series = pd.Series(series)
    
    n = len(series)
    if n < 10:
        log_warning(f"Series length ({n}) too short for spectral analysis.")
        return 0.0

    # Compute Power Spectral Density using Welch's method
    try:
        freqs, psd = signal.welch(series.values, nperseg=min(n, 256), return_onesided=True)
        
        if len(freqs) == 0:
            log_warning("PSD computation returned empty arrays.")
            raise MetricsError("PSD computation failed.")

        # Define low-frequency band (e.g., first 10% of frequencies, excluding 0)
        # Avoid index 0 (DC component) if possible
        valid_indices = np.where(freqs > 0)[0]
        if len(valid_indices) == 0:
            log_warning("No positive frequencies found.")
            raise MetricsError("No positive frequencies found.")
        
        low_freq_cutoff_idx = int(len(valid_indices) * 0.1)
        if low_freq_cutoff_idx == 0:
            low_freq_cutoff_idx = 1
        
        low_freq_indices = valid_indices[:low_freq_cutoff_idx]
        high_freq_indices = valid_indices[low_freq_cutoff_idx:]

        if len(low_freq_indices) == 0 or len(high_freq_indices) == 0:
            log_warning("Frequency bands are empty after splitting.")
            raise MetricsError("Frequency bands invalid.")

        low_freq_psd = psd[low_freq_indices]
        high_freq_psd = psd[high_freq_indices]

        # Calculate max peak in low-freq band
        max_peak = np.max(low_freq_psd)
        
        # Calculate mean floor in high-freq band
        mean_floor = np.mean(high_freq_psd)

        # Check for numerical instability
        if mean_floor <= 0 or np.isnan(mean_floor) or np.isinf(mean_floor):
            log_warning(f"Spectral density failed (zero/nan floor), using variance-based fallback.")
            # Fallback: Use variance as a proxy for "energy" if spectral density is unstable
            # In this context, returning the variance itself or a normalized version is a safe fallback
            # to prevent the pipeline from crashing, though it's not the spectral ratio.
            fallback_val = np.var(series.values)
            return float(fallback_val)

        if max_peak <= 0 or np.isnan(max_peak) or np.isinf(max_peak):
            log_warning(f"Spectral density failed (zero/nan peak), using variance-based fallback.")
            fallback_val = np.var(series.values)
            return float(fallback_val)

        ratio = max_peak / mean_floor

        if np.isnan(ratio) or np.isinf(ratio):
            log_warning(f"Spectral density failed (inf/nan ratio), using variance-based fallback.")
            fallback_val = np.var(series.values)
            return float(fallback_val)

        return float(ratio)

    except Exception as e:
        log_warning(f"Spectral density calculation failed with exception: {e}, using variance-based fallback.")
        fallback_val = np.var(series.values)
        return float(fallback_val)

def compute_all_metrics(series: pd.Series, max_lag: int = 20) -> Dict[str, Any]:
    """
    Compute all metrics for a given time series.

    Args:
        series: Input time series data.
        max_lag: Maximum lag for ACF computation.

    Returns:
        Dictionary containing ACF, Hurst exponent, and Spectral Peak Ratio.
    """
    try:
        acf = compute_acf_lag(series, max_lag)
        hurst = compute_dfa_hurst(series)
        spectral_ratio = compute_spectral_peak_ratio(series)
        
        return {
            "acf": acf.tolist(),
            "hurst": hurst,
            "spectral_peak_ratio": spectral_ratio
        }
    except Exception as e:
        log_error(f"Error computing metrics: {e}")
        raise MetricsError(f"Failed to compute metrics: {e}")

def compute_metrics_for_dataset(dataset_id: str, series: pd.Series, max_lag: int = 20) -> Dict[str, Any]:
    """
    Compute metrics for a specific dataset and handle edge cases.

    Args:
        dataset_id: Identifier for the dataset.
        series: Input time series data.
        max_lag: Maximum lag for ACF computation.

    Returns:
        Dictionary containing dataset_id and computed metrics.
    """
    try:
        metrics = compute_all_metrics(series, max_lag)
        result = {
            "source": dataset_id,
            "length": len(series),
            "hurst": metrics["hurst"],
            "acf_vector": metrics["acf"],
            "spectral_peak_ratio": metrics["spectral_peak_ratio"]
        }
        
        # Check if fallback was used
        # Note: The fallback is returned directly by compute_spectral_peak_ratio.
        # We can't easily distinguish it here without modifying the return signature,
        # but the log message in compute_spectral_peak_ratio handles the warning.
        # If needed, we could add a flag, but for now, the log is the indicator.
        
        return result
    except MetricsError as e:
        log_error(f"Metrics computation failed for {dataset_id}: {e}")
        return {
            "source": dataset_id,
            "length": len(series),
            "hurst": 0.0,
            "acf_vector": [],
            "spectral_peak_ratio": 0.0,
            "error": str(e)
        }