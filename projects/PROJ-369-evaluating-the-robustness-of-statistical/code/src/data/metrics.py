import numpy as np
import pandas as pd
from scipy import signal
from scipy.stats import linregress
from typing import Dict, Any, Union, List, Optional
import logging

logger = logging.getLogger(__name__)

class MetricsError(Exception):
    """Custom exception for metrics calculation errors."""
    pass

def compute_acf_lag(series: pd.Series, max_lag: int = 20) -> List[float]:
    """
    Compute Autocorrelation Function (ACF) vector for lags 0 to max_lag.
    
    Args:
        series: Input time series
        max_lag: Maximum lag to compute (default 20)
        
    Returns:
        List of ACF values for lags 0 to max_lag
    """
    try:
        n = len(series)
        if n <= max_lag:
            logger.warning(f"Series length {n} is too short for max_lag {max_lag}")
            return [0.0] * (max_lag + 1)
        
        # Center the series
        centered = series - series.mean()
        
        acf_values = []
        for lag in range(max_lag + 1):
            if lag == 0:
                acf_values.append(1.0)
            else:
                numerator = np.sum(centered[:-lag] * centered[lag:])
                denominator = np.sum(centered ** 2)
                if denominator == 0:
                    acf_values.append(0.0)
                else:
                    acf_values.append(float(numerator / denominator))
        
        return acf_values
    except Exception as e:
        raise MetricsError(f"Failed to compute ACF: {e}")

def compute_dfa_hurst(series: pd.Series) -> float:
    """
    Compute Hurst exponent using Detrended Fluctuation Analysis (DFA).
    
    Note: Per Spec FR-002, this is excluded from the main preprocessing path
    but kept for reference/alternative analysis.
    
    Args:
        series: Input time series
        
    Returns:
        Hurst exponent estimate
    """
    try:
        n = len(series)
        if n < 100:
            logger.warning("Series too short for reliable DFA")
            return 0.5
        
        # Cumulative sum (profile)
        y = np.cumsum(series - np.mean(series))
        
        # Define window sizes (scales)
        scales = np.logspace(1, np.log10(n/4), num=10).astype(int)
        scales = scales[scales > 4]
        
        fluctuation = []
        for scale in scales:
            # Split into non-overlapping segments
            num_segments = n // scale
            if num_segments == 0:
                continue
            
            # Detrend each segment
            f2 = []
            for i in range(num_segments):
                start = i * scale
                end = (i + 1) * scale
                segment = y[start:end]
                
                # Linear fit
                x = np.arange(scale)
                coeffs = np.polyfit(x, segment, 1)
                trend = np.polyval(coeffs, x)
                detrended = segment - trend
                f2.append(np.mean(detrended ** 2))
            
            if f2:
                fluctuation.append(np.sqrt(np.mean(f2)))
        
        if len(fluctuation) < 2:
            return 0.5
        
        # Fit power law: F(s) ~ s^H
        log_scales = np.log(scales[:len(fluctuation)])
        log_fluctuation = np.log(fluctuation)
        
        slope, _, _, _, _ = linregress(log_scales, log_fluctuation)
        return float(slope)
    except Exception as e:
        logger.warning(f"DFA Hurst calculation failed: {e}")
        return 0.5

def compute_spectral_peak_ratio(series: pd.Series) -> float:
    """
    Compute Spectral Density Peak Ratio.
    
    Algorithm: 
    - Compute PSD using Welch's method
    - Low-freq band: first 10% of frequencies (excluding DC)
    - High-freq band: last 50% of frequencies
    - Ratio = max(PSD in low-freq) / mean(PSD in high-freq)
    
    Args:
        series: Input time series
        
    Returns:
        Spectral density peak ratio
    """
    try:
        n = len(series)
        if n < 100:
            logger.warning("Series too short for spectral analysis")
            return 0.0
        
        # Compute PSD using Welch's method
        f, psd = signal.welch(series, fs=1.0, nperseg=min(256, n))
        
        # Exclude DC component (index 0)
        f = f[1:]
        psd = psd[1:]
        
        if len(f) == 0:
            return 0.0
        
        # Define bands
        n_freqs = len(f)
        low_freq_end = max(1, int(n_freqs * 0.1))
        high_freq_start = int(n_freqs * 0.5)
        
        if high_freq_start >= n_freqs or low_freq_end <= 0:
            return 0.0
        
        low_freq_psd = psd[:low_freq_end]
        high_freq_psd = psd[high_freq_start:]
        
        if len(high_freq_psd) == 0 or np.mean(high_freq_psd) == 0:
            return 0.0
        
        peak_ratio = float(np.max(low_freq_psd) / np.mean(high_freq_psd))
        return peak_ratio
    except Exception as e:
        logger.warning(f"Spectral density calculation failed: {e}")
        raise MetricsError(f"Spectral density failed: {e}")

def compute_all_metrics(series: pd.Series, source: str, series_id: str) -> Dict[str, Any]:
    """
    Compute all metrics for a single series.
    
    This function implements the fallback logic for T051:
    If spectral peak ratio fails, compute variance of residuals as fallback.
    
    Args:
        series: Input time series
        source: Data source name
        series_id: Unique identifier for the series
        
    Returns:
        Dictionary containing all computed metrics
    """
    try:
        # Compute ACF vector
        acf_vector = compute_acf_lag(series, max_lag=20)
        max_acf_lag = max(abs(lag) for lag in acf_vector[1:]) if len(acf_vector) > 1 else 0.0
        
        # Compute Hurst exponent
        hurst = compute_dfa_hurst(series)
        
        # Compute spectral density peak ratio with fallback
        spectral_peak_ratio = None
        variance_fallback = None
        
        try:
            spectral_peak_ratio = compute_spectral_peak_ratio(series)
        except MetricsError as e:
            logger.warning(f"Spectral density failed for {series_id}, using variance-based fallback")
            # Fallback: compute variance of the series (residuals)
            variance_fallback = float(np.var(series))
            spectral_peak_ratio = 0.0  # Mark as failed but provide a value
        
        return {
            "source": source,
            "series_id": series_id,
            "length": len(series),
            "hurst": hurst,
            "acf_vector": acf_vector,
            "max_acf_lag": max_acf_lag,
            "spectral_peak_ratio": spectral_peak_ratio,
            "variance_fallback": variance_fallback
        }
    except Exception as e:
        logger.error(f"Failed to compute all metrics for {series_id}: {e}")
        raise

def compute_metrics_for_dataset(df: pd.DataFrame, source: str, series_id: str) -> Dict[str, Any]:
    """
    Compute metrics for a preprocessed dataset (DataFrame).
    
    Args:
        df: Preprocessed DataFrame with numeric values
        source: Data source name
        series_id: Unique identifier
        
    Returns:
        Dictionary containing all computed metrics
    """
    try:
        # Extract numeric series, handling potential multi-index or columns
        if isinstance(df, pd.DataFrame):
            # If DataFrame, assume single column or aggregate
            if len(df.columns) == 1:
                series = df.iloc[:, 0]
            else:
                # Take mean across columns if multiple
                series = df.mean(axis=1)
        else:
            series = df
        
        # Ensure no NaN values
        series = series.dropna()
        
        if len(series) < 25:
            logger.warning(f"Skipping dataset {series_id}: length < 25")
            return {
                "source": source,
                "series_id": series_id,
                "length": len(series),
                "status": "skipped",
                "reason": "length < 25"
            }
        
        return compute_all_metrics(series, source, series_id)
    except Exception as e:
        logger.error(f"Failed to compute metrics for dataset {series_id}: {e}")
        raise