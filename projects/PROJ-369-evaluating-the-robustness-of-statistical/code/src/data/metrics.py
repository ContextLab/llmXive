"""
Metrics computation module for time series analysis.

Implements:
- Autocorrelation Function (ACF) at lag 20
- Hurst Exponent via Detrended Fluctuation Analysis (DFA)
- Spectral Density Peak Ratio
"""

import numpy as np
import pandas as pd
from scipy import signal
from scipy.stats import linregress
from typing import Dict, Any, Union, List, Optional
import logging

# Import logger from project utils
from src.utils.logging import get_logger

logger = get_logger(__name__)


class MetricsError(Exception):
    """Custom exception for metrics computation errors."""
    pass


def compute_acf_lag(series: Union[np.ndarray, pd.Series], max_lag: int = 20) -> float:
    """
    Compute the Autocorrelation Function (ACF) at a specific lag.

    Args:
        series: Input time series data.
        max_lag: The lag at which to compute the ACF (default 20).

    Returns:
        The ACF value at the specified lag.

    Raises:
        MetricsError: If the series is too short or contains NaN/Inf.
    """
    if not isinstance(series, np.ndarray):
        series = np.asarray(series)

    # Validation
    if np.any(np.isnan(series)) or np.any(np.isinf(series)):
        raise MetricsError("Input series contains NaN or Inf values.")

    n = len(series)
    if n <= max_lag:
        raise MetricsError(f"Series length ({n}) must be greater than max_lag ({max_lag}).")

    # Normalize series (subtract mean, divide by std)
    mean = np.mean(series)
    std = np.std(series)
    if std == 0:
        return 0.0

    normalized = (series - mean) / std

    # Compute ACF at specific lag manually to avoid bias in small samples
    # ACF(k) = sum((x_t - mean)(x_{t+k} - mean)) / sum((x_t - mean)^2)
    numerator = np.sum(normalized[:-max_lag] * normalized[max_lag:])
    denominator = np.sum(normalized ** 2)

    if denominator == 0:
        return 0.0

    return numerator / denominator


def compute_dfa_hurst(series: Union[np.ndarray, pd.Series], scales: Optional[List[int]] = None) -> float:
    """
    Compute the Hurst exponent using Detrended Fluctuation Analysis (DFA).

    Args:
        series: Input time series data.
        scales: List of window sizes (scales) to use for DFA. If None, defaults to
                a geometric progression from 4 to n/4.

    Returns:
        The estimated Hurst exponent (slope of log-log plot).

    Raises:
        MetricsError: If the series is too short or computation fails.
    """
    if not isinstance(series, np.ndarray):
        series = np.asarray(series)

    n = len(series)
    if n < 10:
        raise MetricsError("Series too short for DFA analysis (need at least 10 points).")

    if np.any(np.isnan(series)) or np.any(np.isinf(series)):
        raise MetricsError("Input series contains NaN or Inf values.")

    # Define scales if not provided
    if scales is None:
        # Generate scales from 4 to n/4
        min_scale = 4
        max_scale = n // 4
        if max_scale < min_scale:
            raise MetricsError("Series too short to define valid scales for DFA.")
        scales = list(range(min_scale, max_scale + 1))

    # 1. Profile (Cumulative sum of deviations from mean)
    mean = np.mean(series)
    profile = np.cumsum(series - mean)

    fluctuation_values = []
    valid_scales = []

    for scale in scales:
        if scale * 2 > n:
            continue

        # Divide profile into non-overlapping segments of length 'scale'
        n_segments = n // scale
        fluctuation_sum = 0.0

        for seg_idx in range(n_segments):
            start = seg_idx * scale
            end = start + scale
            segment = profile[start:end]

            # Fit a linear trend to the segment
            x = np.arange(scale)
            coeffs = np.polyfit(x, segment, 1)
            trend = np.polyval(coeffs, x)

            # Detrend
            detrended = segment - trend

            # Calculate RMS fluctuation
            fluctuation = np.sqrt(np.mean(detrended ** 2))
            fluctuation_sum += fluctuation ** 2

        # Average fluctuation for this scale
        F = np.sqrt(fluctuation_sum / n_segments)
        if F > 0:
            fluctuation_values.append(F)
            valid_scales.append(scale)

    if len(valid_scales) < 2:
        raise MetricsError("Not enough valid scales to perform linear regression for Hurst exponent.")

    # 2. Log-log regression
    log_scales = np.log(valid_scales)
    log_fluctuations = np.log(fluctuation_values)

    try:
        slope, _, _, _, _ = linregress(log_scales, log_fluctuations)
    except Exception as e:
        raise MetricsError(f"Linear regression failed during DFA: {e}")

    return slope


def compute_spectral_peak_ratio(series: Union[np.ndarray, pd.Series]) -> float:
    """
    Compute the Spectral Density Peak Ratio.

    This metric compares the power at the dominant frequency to the average power
    in the low-frequency band, indicating the strength of periodic components.

    Args:
        series: Input time series data.

    Returns:
        The ratio of the peak spectral density to the mean spectral density
        in the low-frequency band (excluding DC).

    Raises:
        MetricsError: If the series is too short or FFT fails.
    """
    if not isinstance(series, np.ndarray):
        series = np.asarray(series)

    n = len(series)
    if n < 16:
        raise MetricsError("Series too short for spectral analysis (need at least 16 points).")

    if np.any(np.isnan(series)) or np.any(np.isinf(series)):
        raise MetricsError("Input series contains NaN or Inf values.")

    # Compute FFT
    try:
        fft_vals = np.fft.rfft(series)
        power_spectrum = np.abs(fft_vals) ** 2
    except Exception as e:
        raise MetricsError(f"FFT computation failed: {e}")

    if len(power_spectrum) < 4:
        raise MetricsError("FFT result too short for peak analysis.")

    # Identify peak frequency (excluding DC component at index 0)
    # We look for the maximum in the range [1, len/2]
    peak_idx = np.argmax(power_spectrum[1:]) + 1
    peak_power = power_spectrum[peak_idx]

    # Define low-frequency band for averaging (e.g., indices 1 to 10, or up to n/10)
    # We want to measure "background" power in low frequencies, excluding the peak if it's low freq
    # Let's take the first 10% of frequencies (excluding DC) as the low-freq band
    low_freq_band_size = max(2, int(n * 0.1))
    low_freq_indices = list(range(1, min(low_freq_band_size + 1, len(power_spectrum))))

    # Ensure we don't include the peak in the average if it falls in the low band
    # But for a simple ratio, we can just average the low band and compare to global max
    # Or specifically, ratio of peak to mean of low-freq band
    if not low_freq_indices:
        return 1.0

    mean_low_freq_power = np.mean(power_spectrum[low_freq_indices])

    if mean_low_freq_power == 0:
        return float('inf') if peak_power > 0 else 0.0

    return peak_power / mean_low_freq_power


def compute_all_metrics(series: Union[np.ndarray, pd.Series], max_lag: int = 20) -> Dict[str, Any]:
    """
    Compute all required metrics for a single time series.

    Args:
        series: Input time series data.
        max_lag: Lag for ACF calculation (default 20).

    Returns:
        Dictionary containing:
            - 'acf_lag_20': ACF value at lag 20
            - 'hurst_exponent': DFA-based Hurst exponent
            - 'spectral_peak_ratio': Spectral density peak ratio

    Raises:
        MetricsError: If any metric computation fails.
    """
    try:
        acf_val = compute_acf_lag(series, max_lag)
        hurst_val = compute_dfa_hurst(series)
        spec_ratio = compute_spectral_peak_ratio(series)

        return {
            "acf_lag_20": float(acf_val),
            "hurst_exponent": float(hurst_val),
            "spectral_peak_ratio": float(spec_ratio)
        }
    except MetricsError:
        raise
    except Exception as e:
        raise MetricsError(f"Unexpected error during metrics computation: {e}")


def compute_metrics_for_dataset(dataset_path: str, max_lag: int = 20) -> Dict[str, Any]:
    """
    Load a dataset from a CSV file and compute all metrics.

    Args:
        dataset_path: Path to the CSV file containing the time series.
                      Assumes the file has a 'value' or 'close' column, or is a single column.
        max_lag: Lag for ACF calculation.

    Returns:
        Dictionary with dataset path and computed metrics.

    Raises:
        MetricsError: If file loading or metrics computation fails.
    """
    try:
        df = pd.read_csv(dataset_path)
    except Exception as e:
        raise MetricsError(f"Failed to load dataset from {dataset_path}: {e}")

    # Identify the time series column
    # Prioritize 'value', 'close', 'price', or the first numeric column
    target_col = None
    candidates = ['value', 'close', 'price', 'adjusted_close', 'Adj Close']
    for cand in candidates:
        if cand in df.columns:
            target_col = cand
            break

    if target_col is None:
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            target_col = numeric_cols[0]
        else:
            raise MetricsError(f"No numeric column found in {dataset_path}")

    series_data = df[target_col].dropna().values

    if len(series_data) < 20:
        logger.warning(f"Series from {dataset_path} too short after cleaning. Skipping metrics.")
        return {
            "dataset_path": dataset_path,
            "error": "Series too short",
            "metrics": None
        }

    try:
        metrics = compute_all_metrics(series_data, max_lag)
        return {
            "dataset_path": dataset_path,
            "metrics": metrics
        }
    except MetricsError as e:
        logger.warning(f"Metrics computation failed for {dataset_path}: {e}")
        return {
            "dataset_path": dataset_path,
            "error": str(e),
            "metrics": None
        }