import numpy as np
import pandas as pd
from scipy import signal
from scipy.stats import linregress
from typing import Dict, Any, Union, List, Optional
import logging

from src.utils.logging import get_logger

logger = get_logger(__name__)


class MetricsError(Exception):
    """Custom exception for metrics computation errors."""
    pass


def compute_acf_lag(series: Union[pd.Series, np.ndarray], max_lag: int = 20) -> Dict[int, float]:
    """
    Compute the Autocorrelation Function (ACF) up to a specified lag.

    Args:
        series: Input time series data.
        max_lag: Maximum lag to compute (default 20).

    Returns:
        Dictionary mapping lag index to correlation coefficient.

    Raises:
        MetricsError: If input is invalid or computation fails.
    """
    if series is None or len(series) == 0:
        raise MetricsError("Input series cannot be None or empty.")

    try:
        # Ensure numpy array for calculation
        if isinstance(series, pd.Series):
            data = series.values
        else:
            data = np.asarray(series)

        # Handle NaNs by dropping them
        data = data[~np.isnan(data)]

        if len(data) < max_lag + 1:
            logger.warning(f"Series length ({len(data)}) is less than max_lag ({max_lag}). "
                           f"Reducing max_lag to {len(data) - 1}.")
            max_lag = len(data) - 1

        if max_lag < 1:
            raise MetricsError("Series too short to compute any lag correlations.")

        # Compute ACF using scipy's correlate
        # Normalize by variance (ddof=0 for population variance consistent with standard ACF)
        mean_val = np.mean(data)
        var_val = np.var(data)
        
        if var_val == 0:
            # Constant series, all correlations are 0 (or undefined, but 0 is safe for stats)
            return {lag: 0.0 for lag in range(1, max_lag + 1)}

        # Calculate ACF manually for precision control
        # ACF(k) = Cov(X_t, X_{t+k}) / Var(X_t)
        acf_values = {}
        for lag in range(1, max_lag + 1):
            # Overlap
            x1 = data[:-lag]
            x2 = data[lag:]
            
            cov = np.mean((x1 - mean_val) * (x2 - mean_val))
            acf_values[lag] = cov / var_val

        return acf_values

    except Exception as e:
        logger.error(f"Error computing ACF: {e}")
        raise MetricsError(f"ACF computation failed: {e}")


def compute_dfa_hurst(series: Union[pd.Series, np.ndarray], min_scale: int = 4, max_scale: Optional[int] = None) -> float:
    """
    Compute the Hurst exponent using Detrended Fluctuation Analysis (DFA).

    Args:
        series: Input time series data.
        min_scale: Minimum window size for DFA (default 4).
        max_scale: Maximum window size (default: 1/4 of series length).

    Returns:
        Estimated Hurst exponent (H).

    Raises:
        MetricsError: If input is invalid or computation fails.
    """
    if series is None or len(series) == 0:
        raise MetricsError("Input series cannot be None or empty.")

    try:
        if isinstance(series, pd.Series):
            data = series.values
        else:
            data = np.asarray(series)

        # Remove NaNs
        data = data[~np.isnan(data)]
        n = len(data)

        if n < min_scale * 2:
            raise MetricsError(f"Series length ({n}) is too short for DFA with min_scale={min_scale}.")

        if max_scale is None:
            max_scale = max(min_scale, n // 4)

        # 1. Profile: Cumulative sum of deviations from mean
        mean_val = np.mean(data)
        profile = np.cumsum(data - mean_val)

        # 2. Define scales (window sizes)
        # Use a logarithmic spacing of scales
        scales = np.unique(np.logspace(np.log10(min_scale), np.log10(max_scale), num=20).astype(int))
        scales = scales[scales > min_scale] # Ensure strictly greater than min if possible, but keep min if needed
        if len(scales) == 0:
            scales = np.array([min_scale])
        
        fluctuation_sizes = []

        for scale in scales:
            # 3. Divide profile into non-overlapping boxes of size 'scale'
            n_boxes = int(n // scale)
            if n_boxes == 0:
                continue

            # Calculate fluctuation for each box
            rms_fluctuation = 0.0
            count = 0

            for i in range(n_boxes):
                # Extract segment
                start_idx = i * scale
                end_idx = start_idx + scale
                segment = profile[start_idx:end_idx]

                # Fit linear trend (detrending)
                x = np.arange(scale)
                # Linear regression: y = mx + c
                # Using least squares
                A = np.vstack([x, np.ones(scale)]).T
                m, c = np.linalg.lstsq(A, segment, rcond=None)[0]
                
                # Subtract trend
                trend = m * x + c
                detrended_segment = segment - trend

                # RMS fluctuation for this box
                rms_fluctuation += np.sqrt(np.mean(detrended_segment**2))
                count += 1

            if count > 0:
                rms_fluctuation = np.sqrt(rms_fluctuation / count)
                fluctuation_sizes.append(rms_fluctuation)
            else:
                # If no boxes fit, skip this scale
                continue

        if len(fluctuation_sizes) < 2:
            raise MetricsError("Not enough valid scales computed for linear regression in DFA.")

        # 4. Fit power law: F(s) ~ s^H  =>  log(F) = H * log(s) + C
        log_scales = np.log(scales[:len(fluctuation_sizes)])
        log_fluctuation = np.log(fluctuation_sizes)

        # Linear regression to find slope (Hurst exponent)
        slope, _, _, _, _ = linregress(log_scales, log_fluctuation)
        
        hurst = float(slope)
        return hurst

    except Exception as e:
        logger.error(f"Error computing DFA Hurst exponent: {e}")
        raise MetricsError(f"DFA Hurst computation failed: {e}")


def compute_spectral_peak_ratio(series: Union[pd.Series, np.ndarray], min_freq_ratio: float = 0.01) -> float:
    """
    Compute the Spectral Density Peak Ratio.
    
    This metric identifies the ratio of the dominant peak power to the average 
    power in the non-peak frequencies (or the noise floor), indicating 
    periodicity strength.
    
    Steps:
    1. Compute PSD using Welch's method.
    2. Identify the dominant peak (excluding DC if necessary).
    3. Calculate the ratio of peak power to the median/mean of the rest.

    Args:
        series: Input time series data.
        min_freq_ratio: Minimum frequency to consider as a peak (fraction of Nyquist).

    Returns:
        Ratio of dominant peak power to the background noise floor.
        Returns 0.0 if no significant peak is found or computation fails.

    Raises:
        MetricsError: If input is invalid.
    """
    if series is None or len(series) == 0:
        raise MetricsError("Input series cannot be None or empty.")

    try:
        if isinstance(series, pd.Series):
            data = series.values
        else:
            data = np.asarray(series)

        # Remove NaNs
        data = data[~np.isnan(data)]
        n = len(data)

        if n < 10:
            logger.warning("Series too short for spectral analysis. Returning 0.0.")
            return 0.0

        # Compute Power Spectral Density using Welch's method
        # fs is assumed to be 1.0 for relative frequency analysis
        f, Pxx = signal.welch(data, fs=1.0, nperseg=min(256, n), scaling='density')

        if len(f) == 0:
            return 0.0

        # Filter out DC component (f=0) and very low frequencies if desired
        # Usually, we look for peaks above a certain frequency fraction
        valid_mask = f > (f[-1] * min_freq_ratio) # Ignore near-DC
        if not np.any(valid_mask):
            valid_mask = np.ones_like(f, dtype=bool) # Fallback to all if none valid

        f_valid = f[valid_mask]
        Pxx_valid = Pxx[valid_mask]

        if len(Pxx_valid) == 0:
            return 0.0

        # Find the maximum power (peak)
        peak_power = np.max(Pxx_valid)
        peak_idx = np.argmax(Pxx_valid)

        # Define "background" as the median power of the rest of the spectrum
        # Exclude the peak and its immediate neighbors to avoid leakage affecting the floor
        neighbor_count = 2
        start_idx = max(0, peak_idx - neighbor_count)
        end_idx = min(len(Pxx_valid), peak_idx + neighbor_count + 1)
        
        background_indices = np.concatenate([
            np.arange(0, start_idx),
            np.arange(end_idx, len(Pxx_valid))
        ])

        if len(background_indices) == 0:
            # Fallback: use median of all valid if we can't exclude neighbors
            background_power = np.median(Pxx_valid)
        else:
            background_power = np.median(Pxx_valid[background_indices])

        if background_power <= 0:
            # Avoid division by zero or negative noise floor
            return 0.0

        ratio = peak_power / background_power
        return float(ratio)

    except Exception as e:
        logger.error(f"Error computing spectral peak ratio: {e}")
        raise MetricsError(f"Spectral peak ratio computation failed: {e}")


def compute_all_metrics(series: Union[pd.Series, np.ndarray]) -> Dict[str, Any]:
    """
    Compute all defined metrics for a given time series.

    Args:
        series: Input time series data.

    Returns:
        Dictionary containing:
          - 'acf_lag': Dict of lag -> correlation
          - 'hurst': Float (DFA)
          - 'spectral_peak_ratio': Float

    Raises:
        MetricsError: If any metric computation fails.
    """
    try:
        # Compute ACF (lag 20)
        acf_result = compute_acf_lag(series, max_lag=20)
        
        # Compute Hurst (DFA)
        hurst_result = compute_dfa_hurst(series)
        
        # Compute Spectral Peak Ratio
        spectral_result = compute_spectral_peak_ratio(series)

        return {
            "acf_lag": acf_result,
            "hurst": hurst_result,
            "spectral_peak_ratio": spectral_result
        }
    except MetricsError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in compute_all_metrics: {e}")
        raise MetricsError(f"General metrics computation failed: {e}")


def compute_metrics_for_dataset(
    dataset_path: str,
    time_column: str = 'date',
    value_column: str = 'value'
) -> Dict[str, Any]:
    """
    Load a dataset from a file and compute metrics for the specified value column.

    Args:
        dataset_path: Path to the CSV file.
        time_column: Name of the time column (for parsing if needed).
        value_column: Name of the column containing the time series values.

    Returns:
        Dictionary with metrics and metadata.

    Raises:
        MetricsError: If file loading or metric computation fails.
    """
    try:
        logger.info(f"Loading dataset from {dataset_path}")
        df = pd.read_csv(dataset_path)

        if value_column not in df.columns:
            raise MetricsError(f"Column '{value_column}' not found in {dataset_path}. "
                               f"Available columns: {list(df.columns)}")

        series = df[value_column]

        # Check for minimum length
        if len(series.dropna()) < 20:
            logger.warning(f"Series in {dataset_path} too short for robust metrics.")
            # We still attempt computation, but it might be unreliable

        metrics = compute_all_metrics(series)
        
        metrics['dataset_path'] = dataset_path
        metrics['value_column'] = value_column
        metrics['n_points'] = len(series)
        metrics['n_valid'] = series.dropna().count()

        return metrics

    except FileNotFoundError:
        logger.error(f"Dataset file not found: {dataset_path}")
        raise MetricsError(f"Dataset file not found: {dataset_path}")
    except Exception as e:
        logger.error(f"Error processing dataset {dataset_path}: {e}")
        raise MetricsError(f"Dataset processing failed: {e}")
