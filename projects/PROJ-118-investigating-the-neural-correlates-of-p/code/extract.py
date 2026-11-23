"""
Metric extraction pipeline for MMN analysis.

This module handles:
- Loading cleaned epochs
- Computing average ERPs
- Computing difference waves
- Extracting peak amplitude and latency
- Calculating SNR
- Saving metrics to CSV
"""
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
import mne

from config_loader import get_project_root, get_config, ensure_directory
from cleanup_utils import setup_logger, validate_array_shape, safe_divide, log_execution_time

logger = setup_logger(__name__)

# ----------------------------------------------------------------------
# Loading
# ----------------------------------------------------------------------

def get_subject_epochs_paths(epochs_dir: str) -> Dict[str, Path]:
    """
    Get paths to cleaned epochs for each subject.

    Args:
        epochs_dir: Directory containing cleaned epochs.

    Returns:
        Dictionary mapping subject ID to epochs file path.
    """
    epochs_path = Path(epochs_dir)
    subjects = {}
    for f in epochs_path.glob('sub-*_epo_clean.fif'):
        subject_id = f.stem.split('_')[0]
        subjects[subject_id] = f
    return subjects

@log_execution_time()
def load_epochs(epochs_path: Path) -> mne.Epochs:
    """
    Load epochs from a FIF file.

    Args:
        epochs_path: Path to epochs file.

    Returns:
        Epochs object.
    """
    if not epochs_path.exists():
        raise FileNotFoundError(f"Epochs file not found: {epochs_path}")
    epochs = mne.read_epochs(epochs_path, preload=True)
    logger.info(f"Loaded {len(epochs)} epochs from {epochs_path}")
    return epochs

# ----------------------------------------------------------------------
# ERP Computation
# ----------------------------------------------------------------------

@log_execution_time()
def compute_average_erps(epochs: mne.Epochs, conditions: List[str]) -> Dict[str, mne.Evoked]:
    """
    Compute average ERPs for specified conditions.

    Args:
        epochs: Epochs object.
        conditions: List of condition names.

    Returns:
        Dictionary mapping condition to Evoked object.
    """
    erps = {}
    for condition in conditions:
        try:
            evoked = epochs.average(condition=condition)
            erps[condition] = evoked
            logger.info(f"Computed ERP for {condition}: {len(evoked.data[0])} time points")
        except Exception as e:
            logger.warning(f"Could not compute ERP for {condition}: {e}")
    return erps

@log_execution_time()
def compute_difference_wave(standard_evoked: mne.Evoked, deviant_evoked: mne.Evoked) -> mne.Evoked:
    """
    Compute the difference wave (Deviant - Standard).

    Args:
        standard_evoked: Standard condition Evoked.
        deviant_evoked: Deviant condition Evoked.

    Returns:
        Difference wave Evoked.
    """
    # Ensure data shapes match
    if standard_evoked.data.shape != deviant_evoked.data.shape:
        raise ValueError("ERP shapes do not match for difference wave calculation.")

  # Subtract standard from deviant
    diff_data = deviant_evoked.data - standard_evoked.data
    diff_evoked = mne.EvokedArray(
        diff_data,
        standard_evoked.info,
        tmin=standard_evoked.times[0]
    )
    diff_evoked.comment = "Difference Wave (Deviant - Standard)"
    logger.info("Computed difference wave")
    return diff_evoked

# ----------------------------------------------------------------------
# Peak Detection
# ----------------------------------------------------------------------

def extract_erp_metrics(
    evoked: mne.Evoked,
    channels: List[str],
    window: Tuple[float, float],
    polarity: str = 'negative'
) -> Dict[str, Any]:
    """
    Extract peak amplitude and latency from ERP.

    Args:
        evoked: Evoked object.
        channels: List of channels to search.
        window: Time window (tmin, tmax) in seconds.
        polarity: 'negative' or 'positive'.

    Returns:
        Dictionary with peak amplitude, latency, and channel.
    """
    # Filter channels
    available_channels = [ch for ch in channels if ch in evoked.ch_names]
    if not available_channels:
        logger.warning(f"No channels found in {channels}")
        return {'peak_detected': False}

    # Select time indices
    tmin, tmax = window
    time_mask = (evoked.times >= tmin) & (evoked.times <= tmax)
    if not np.any(time_mask):
        logger.warning(f"No time points in window {window}")
        return {'peak_detected': False}

    # Extract data
    data = evoked.data[available_channels][:, time_mask]
    times = evoked.times[time_mask]

    if polarity == 'negative':
        peak_idx = np.unravel_index(np.argmin(data), data.shape)
        amplitude = data[peak_idx]
        latency_idx = np.argmin(data[peak_idx[0]])
        latency = times[latency_idx]
    else:
        peak_idx = np.unravel_index(np.argmax(data), data.shape)
        amplitude = data[peak_idx]
        latency_idx = np.argmax(data[peak_idx[0]])
        latency = times[latency_idx]

    channel = available_channels[peak_idx[0]]
    logger.info(f"Peak found: {amplitude:.3f} µV at {latency:.1f} ms in {channel}")

    return {
        'amplitude': amplitude,
        'latency': latency,
        'channel': channel,
        'peak_detected': True
    }

@log_execution_time()
def calculate_snr(
    evoked: mne.Evoked,
    signal_window: Tuple[float, float],
    noise_window: Tuple[float, float]
) -> float:
    """
    Calculate Signal-to-Noise Ratio (SNR).

    Args:
        evoked: Evoked object.
        signal_window: Time window for signal.
        noise_window: Time window for noise (baseline).

    Returns:
        SNR value.
    """
    # Signal power
    signal_mask = (evoked.times >= signal_window[0]) & (evoked.times <= signal_window[1])
    signal_data = evoked.data[:, signal_mask]
    signal_power = np.mean(signal_data ** 2)

    # Noise power
    noise_mask = (evoked.times >= noise_window[0]) & (evoked.times <= noise_window[1])
    noise_data = evoked.data[:, noise_mask]
    noise_power = np.mean(noise_data ** 2)

    snr = safe_divide(signal_power, noise_power, default=0.0)
    snr_db = 10 * np.log10(snr) if snr > 0 else -np.inf
    logger.info(f"SNR: {snr:.2f} ({snr_db:.2f} dB)")
    return snr_db

# ----------------------------------------------------------------------
# Metrics Extraction
# ----------------------------------------------------------------------

@log_execution_time()
def extract_metrics_for_subject(
    epochs_path: Path,
    channels: List[str],
    primary_window: Tuple[float, float],
    secondary_window: Tuple[float, float],
    threshold: float = 2.0
) -> Dict[str, Any]:
    """
    Extract all metrics for a single subject.

    Args:
        epochs_path: Path to cleaned epochs.
        channels: Channels to analyze.
        primary_window: Primary search window.
        secondary_window: Fallback search window.
        threshold: Minimum amplitude threshold for peak detection.

    Returns:
        Dictionary of metrics.
    """
    epochs = load_epochs(epochs_path)
    erps = compute_average_erps(epochs, ['standard', 'deviant'])

    if 'standard' not in erps or 'deviant' not in erps:
        logger.error("Could not compute ERPs for standard or deviant conditions.")
        return {'peak_detected': False}

    standard_evoked = erps['standard']
    deviant_evoked = erps['deviant']
    diff_evoked = compute_difference_wave(standard_evoked, deviant_evoked)

    # Extract standard metrics
    std_metrics = extract_erp_metrics(standard_evoked, channels, primary_window, 'negative')
    dev_metrics = extract_erp_metrics(deviant_evoked, channels, primary_window, 'negative')

    # Extract difference wave metrics
    diff_metrics = extract_erp_metrics(diff_evoked, channels, primary_window, 'negative')

    # Fallback if no peak in primary window
    if not diff_metrics.get('peak_detected') or abs(diff_metrics['amplitude']) < threshold:
        logger.info(f"Primary window peak not found, trying secondary window: {secondary_window}")
        diff_metrics_fallback = extract_erp_metrics(diff_evoked, channels, secondary_window, 'negative')
        if diff_metrics_fallback.get('peak_detected'):
            diff_metrics = diff_metrics_fallback
        else:
            diff_metrics['peak_detected'] = False

    # Calculate SNR
    snr = calculate_snr(diff_evoked, signal_window=(0.1, 0.25), noise_window=(-0.2, 0.0))

    return {
        'standard_amplitude': std_metrics.get('amplitude'),
        'standard_latency': std_metrics.get('latency'),
        'deviant_amplitude': dev_metrics.get('amplitude'),
        'deviant_latency': dev_metrics.get('latency'),
        'peak_amplitude': diff_metrics.get('amplitude'),
        'peak_latency': diff_metrics.get('latency'),
        'peak_channel': diff_metrics.get('channel'),
        'peak_detected': diff_metrics.get('peak_detected', False),
        'snr': snr
    }

# ----------------------------------------------------------------------
# Output
# ----------------------------------------------------------------------

@log_execution_time()
def save_intermediate_erps(
    erps: Dict[str, mne.Evoked],
    output_path: Path
) -> None:
    """
    Save intermediate ERPs to FIF file.

    Args:
        erps: Dictionary of Evoked objects.
        output_path: Output file path.
    """
    ensure_directory(output_path.parent)
    # Save as a single Evoked object for the difference wave
    if 'diff' in erps:
        erps['diff'].save(output_path, overwrite=True)
    logger.info(f"Saved intermediate ERPs to {output_path}")

@log_execution_time()
def save_metrics_to_csv(metrics: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save extracted metrics to CSV.

    Args:
        metrics: List of metric dictionaries.
        output_path: Output CSV path.
    """
    ensure_directory(output_path.parent)
    df = pd.DataFrame(metrics)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved metrics to {output_path} ({len(df)} rows)")

# ----------------------------------------------------------------------
# Pipeline
# ----------------------------------------------------------------------

@log_execution_time()
def run_extraction_pipeline(
    epochs_dir: str,
    output_dir: str,
    channels: Optional[List[str]] = None,
    primary_window: Tuple[float, float] = (0.1, 0.25),
    secondary_window: Tuple[float, float] = (0.1, 0.3),
    threshold: float = 2.0
) -> Path:
    """
    Run the full metric extraction pipeline.

    Args:
        epochs_dir: Directory with cleaned epochs.
        output_dir: Directory for output files.
        channels: Channels to analyze (default: Fz, FCz).
        primary_window: Primary peak search window.
        secondary_window: Secondary peak search window.
        threshold: Minimum amplitude threshold.

    Returns:
        Path to metrics CSV.
    """
    if channels is None:
        channels = ['Fz', 'FCz']

    epochs_paths = get_subject_epochs_paths(epochs_dir)
    if not epochs_paths:
        logger.error("No epoch files found.")
        raise FileNotFoundError("No epoch files found.")

    all_metrics = []

    for subject_id, epochs_path in epochs_paths.items():
        logger.info(f"Processing {subject_id}...")
        try:
            metrics = extract_metrics_for_subject(
                epochs_path,
                channels,
                primary_window,
                secondary_window,
                threshold
            )
            metrics['participant_id'] = subject_id
            all_metrics.append(metrics)
        except Exception as e:
            logger.error(f"Failed to process {subject_id}: {e}")
            # Still add a row with NaNs to maintain CSV structure
            metrics = {
                'participant_id': subject_id,
                'standard_amplitude': np.nan,
                'standard_latency': np.nan,
                'deviant_amplitude': np.nan,
                'deviant_latency': np.nan,
                'peak_amplitude': np.nan,
                'peak_latency': np.nan,
                'peak_channel': None,
                'peak_detected': False,
                'snr': np.nan
            }
            all_metrics.append(metrics)

    output_path = Path(output_dir) / 'metrics.csv'
    save_metrics_to_csv(all_metrics, output_path)
    return output_path

def main():
    """Main entry point for extraction."""
    project_root = get_project_root()
    epochs_dir = project_root / 'data' / 'processed'
    output_dir = project_root / 'results'

    if not epochs_dir.exists():
        logger.error(f"Epochs directory not found: {epochs_dir}")
        return

    metrics_path = run_extraction_pipeline(str(epochs_dir), str(output_dir))
    logger.info(f"Extraction complete. Metrics saved to {metrics_path}")

if __name__ == "__main__":
    main()
