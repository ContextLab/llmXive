"""
Metrics computation module for statistical robustness evaluation.

This module provides functions to compute:
- Autocorrelation Function (ACF) at lag 20
- Hurst exponent via Detrended Fluctuation Analysis (DFA)
- Spectral density peak ratio
"""
import numpy as np
import pandas as pd
from scipy import signal
from scipy.stats import linregress
from typing import Dict, Any, List, Optional, Tuple
import logging
from pathlib import Path
import json

from src.utils.config import get_path

logger = logging.getLogger(__name__)

def compute_acf_lag20(series: np.ndarray) -> float:
    """
    Compute the Autocorrelation Function (ACF) at lag 20.

    Args:
        series: 1D numpy array of time series data.

    Returns:
        ACF value at lag 20.
    """
    if len(series) < 21:
        logger.warning(f"Series length ({len(series)}) is less than lag 20 + 1. "
                       f"Returning NaN for ACF lag 20.")
        return np.nan

    # Use scipy's correlate to compute ACF
    # Normalize by variance and mean
    series_centered = series - np.mean(series)
    variance = np.var(series)

    if variance == 0:
        return 0.0

    # Compute correlation at lag 20
    n = len(series)
    cov_lag20 = np.mean(series_centered[:n-20] * series_centered[20:])
    acf_lag20 = cov_lag20 / variance

    return float(acf_lag20)

def compute_dfa_hurst(series: np.ndarray, min_length: int = 100) -> float:
    """
    Compute Hurst exponent using Detrended Fluctuation Analysis (DFA).

    Args:
        series: 1D numpy array of time series data.
        min_length: Minimum length required for DFA computation.

    Returns:
        Estimated Hurst exponent.
    """
    if len(series) < min_length:
        logger.warning(f"Series length ({len(series)}) is less than minimum required ({min_length}). "
                       f"Returning NaN for Hurst exponent.")
        return np.nan

    # Remove mean
    y = series - np.mean(series)
    n = len(y)

    # Create profile (cumulative sum)
    profile = np.cumsum(y)

    # Define scales (window sizes)
    # Use a range of scales from 4 to n/4
    scales = []
    for i in range(4, n // 4):
        scales.append(i)

    if not scales:
        logger.warning("No valid scales available for DFA.")
        return np.nan

    # Compute fluctuation for each scale
    fluctuation = []
    for scale in scales:
        # Split profile into segments
        num_segments = n // scale
        if num_segments < 2:
            continue

        rms_values = []
        for seg_idx in range(num_segments):
            start = seg_idx * scale
            end = start + scale
            segment = profile[start:end]

            # Fit a linear trend
            x = np.arange(scale)
            coeffs = np.polyfit(x, segment, 1)
            trend = np.polyval(coeffs, x)

            # Detrended segment
            detrended = segment - trend
            rms = np.sqrt(np.mean(detrended ** 2))
            rms_values.append(rms)

        if rms_values:
            fluctuation.append(np.mean(rms_values))

    if len(fluctuation) < 2:
        logger.warning("Not enough valid scales for DFA regression.")
        return np.nan

    # Log-log regression to estimate Hurst exponent
    log_scales = np.log(scales[:len(fluctuation)])
    log_fluctuation = np.log(fluctuation)

    slope, _, _, _, _ = linregress(log_scales, log_fluctuation)

    return float(slope)

def compute_spectral_density_peak_ratio(series: np.ndarray) -> float:
    """
    Compute the spectral density peak ratio.

    This measures the ratio of the maximum spectral density to the median
    spectral density, indicating the presence of dominant frequencies.

    Args:
        series: 1D numpy array of time series data.

    Returns:
        Spectral density peak ratio.
    """
    if len(series) < 50:
        logger.warning(f"Series length ({len(series)}) is too short for spectral analysis. "
                       f"Returning NaN for spectral density peak ratio.")
        return np.nan

    # Compute FFT
    fft_result = np.fft.fft(series - np.mean(series))
    freqs = np.fft.fftfreq(len(series))

    # Take only positive frequencies
    positive_freq_mask = freqs > 0
    positive_freqs = freqs[positive_freq_mask]
    positive_spectra = np.abs(fft_result[positive_freq_mask]) ** 2

    if len(positive_spectra) == 0:
        return 0.0

    # Compute peak ratio
    max_power = np.max(positive_spectra)
    median_power = np.median(positive_spectra)

    if median_power == 0:
        return float('inf') if max_power > 0 else 0.0

    return float(max_power / median_power)

def compute_all_metrics(series: np.ndarray, series_name: str = "unknown") -> Dict[str, Any]:
    """
    Compute all metrics (ACF lag 20, Hurst exponent, spectral density peak ratio) for a series.

    Args:
        series: 1D numpy array of time series data.
        series_name: Name/identifier of the series for logging.

    Returns:
        Dictionary containing all computed metrics.
    """
    metrics = {
        "series_name": series_name,
        "length": len(series),
        "acf_lag20": compute_acf_lag20(series),
        "hurst_exponent": compute_dfa_hurst(series),
        "spectral_density_peak_ratio": compute_spectral_density_peak_ratio(series)
    }

    logger.info(f"Computed metrics for {series_name}: "
                f"ACF(20)={metrics['acf_lag20']:.4f}, "
                f"H={metrics['hurst_exponent']:.4f}, "
                f"PeakRatio={metrics['spectral_density_peak_ratio']:.4f}")

    return metrics

def compute_metrics_for_all_synthetic_series(
    synthetic_data_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Compute metrics for all synthetic series generated in T019.

    This function loads synthetic data from the generated files and computes
    ACF lag 20, Hurst exponent, and spectral density peak ratio for each series.

    Args:
        synthetic_data_path: Path to the directory containing synthetic data files.
                            Defaults to the project's data/processed/synthetic/ directory.

    Returns:
        List of dictionaries, each containing metrics for one synthetic series.
    """
    if synthetic_data_path is None:
        synthetic_data_path = str(get_path("data_processed") / "synthetic")

    data_path = Path(synthetic_data_path)

    if not data_path.exists():
        logger.error(f"Synthetic data directory does not exist: {data_path}")
        raise FileNotFoundError(f"Synthetic data directory not found: {data_path}")

    all_metrics = []

    # Find all CSV files in the synthetic data directory
    csv_files = list(data_path.glob("*.csv"))

    if not csv_files:
        logger.warning(f"No synthetic data files found in {data_path}")
        return all_metrics

    logger.info(f"Found {len(csv_files)} synthetic data files to process.")

    for csv_file in csv_files:
        try:
            # Load the data
            df = pd.read_csv(csv_file)

            # Identify the time series column (usually the second column after index)
            # Assuming the first column is the index or time, and the rest are data
            if len(df.columns) > 1:
                # Try to find the numeric column
                numeric_cols = df.select_dtypes(include=[np.number]).columns
                if len(numeric_cols) > 0:
                    series_col = numeric_cols[0]
                    series_data = df[series_col].values
                    series_name = f"{csv_file.stem}_{series_col}"
                else:
                    logger.warning(f"No numeric columns found in {csv_file}. Skipping.")
                    continue
            else:
                # Single column data
                series_data = df.iloc[:, 0].values
                series_name = csv_file.stem

            # Compute metrics
            metrics = compute_all_metrics(series_data, series_name)
            metrics["source_file"] = str(csv_file)
            all_metrics.append(metrics)

        except Exception as e:
            logger.error(f"Error processing {csv_file}: {e}")
            continue

    return all_metrics

def save_metrics_to_json(
    metrics_list: List[Dict[str, Any]],
    output_path: Optional[str] = None
) -> str:
    """
    Save computed metrics to a JSON file.

    Args:
        metrics_list: List of metric dictionaries.
        output_path: Path for the output JSON file. Defaults to results/metrics/synthetic_metrics.json.

    Returns:
        Path to the saved JSON file.
    """
    if output_path is None:
        output_path = str(get_path("results") / "metrics" / "synthetic_metrics.json")

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(metrics_list, f, indent=2)

    logger.info(f"Saved metrics for {len(metrics_list)} series to {output_file}")
    return str(output_file)

def main():
    """
    Main entry point to compute metrics for all synthetic series.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger.info("Starting metric computation for synthetic series...")

    try:
        # Compute metrics for all synthetic series
        metrics = compute_metrics_for_all_synthetic_series()

        if not metrics:
            logger.warning("No metrics computed. Check synthetic data files.")
            return

        # Save results
        output_path = save_metrics_to_json(metrics)

        # Print summary
        logger.info(f"Computed metrics for {len(metrics)} synthetic series.")
        logger.info(f"Results saved to: {output_path}")

        # Print sample metrics
        for i, m in enumerate(metrics[:3]):
            logger.info(f"Sample {i+1}: {m['series_name']} - "
                        f"ACF(20)={m['acf_lag20']:.4f}, "
                        f"H={m['hurst_exponent']:.4f}, "
                        f"PeakRatio={m['spectral_density_peak_ratio']:.4f}")

    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise

if __name__ == "__main__":
    main()