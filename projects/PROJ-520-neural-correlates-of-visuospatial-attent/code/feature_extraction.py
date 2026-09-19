import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import mne
from mne.time_frequency import tfr_morlet

from logger import get_logger
from config import get_config

logger = get_logger(__name__)

# --- Helper Functions ---

def load_epochs(path: str) -> mne.Epochs:
    """Load preprocessed epochs from a FIF file."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Epochs file not found: {path}")
    logger.info(f"Loading epochs from {path}")
    return mne.read_epochs(str(p), preload=True)

def compute_time_frequency(
    epochs: mne.Epochs,
    freqs: np.ndarray,
    n_cycles: List[float],
    use_fft: bool = False
) -> mne.time_frequency.AverageTFR:
    """
    Compute Morlet wavelet time-frequency decomposition.
    
    Args:
        epochs: Preprocessed MNE epochs object.
        freqs: Array of frequencies to compute.
        n_cycles: Number of cycles for each frequency (can be scalar or list).
        use_fft: Whether to use FFT for computation (not used for Morlet).
        
    Returns:
        TFR object containing power estimates.
    """
    logger.info(f"Computing time-frequency decomposition for {len(freqs)} frequencies")
    # Ensure n_cycles matches freqs length if it's a list
    if isinstance(n_cycles, list) and len(n_cycles) != len(freqs):
        raise ValueError("n_cycles length must match freqs length")
    
    tfr = tfr_morlet(
        epochs, 
        freqs=freqs, 
        n_cycles=n_cycles, 
        use_fft=use_fft,
        decim=1,
        return_itc=False,
        average=False
    )
    return tfr

def baseline_normalize(
    tfr: mne.time_frequency.AverageTFR,
    baseline: Tuple[float, float],
    mode: str = 'logratio'
) -> mne.time_frequency.AverageTFR:
    """
    Apply baseline normalization to TFR data.
    
    Args:
        tfr: TFR object from compute_time_frequency.
        baseline: Tuple of (start_time, end_time) in seconds.
        mode: Normalization mode ('logratio', 'ratio', 'zscore', etc.)
        
    Returns:
        Normalized TFR object.
    """
    logger.info(f"Applying baseline normalization with mode '{mode}' and baseline {baseline}")
    tfr.apply_baseline(baseline=baseline, mode=mode)
    return tfr

def baseline_normalize_with_times(
    tfr: mne.time_frequency.AverageTFR,
    baseline: Tuple[float, float] = (-1.0, 0.0),
    mode: str = 'logratio'
) -> mne.time_frequency.AverageTFR:
    """
    Wrapper for baseline_normalize with explicit time defaults.
    """
    return baseline_normalize(tfr, baseline, mode)

def extract_mean_power(
    epochs: mne.Epochs,
    tfr: mne.time_frequency.AverageTFR,
    freq_band: Tuple[float, float],
    ch_names: List[str],
    time_window: Tuple[float, float]
) -> np.ndarray:
    """
    Extract mean power for a specific frequency band, channels, and time window.
    
    Args:
        epochs: MNE Epochs object (used for channel info).
        tfr: Normalized TFR object.
        freq_band: Tuple of (low_freq, high_freq) in Hz.
        ch_names: List of channel names to average over.
        time_window: Tuple of (start_time, end_time) in seconds.
        
    Returns:
        2D array of shape (n_epochs, 1) containing mean power values.
    """
    # Validate channels exist in the data
    available_chs = set(epochs.ch_names)
    requested_chs = set(ch_names)
    missing = requested_chs - available_chs
    if missing:
        logger.warning(f"Requested channels not found in data: {missing}. Skipping.")
        # Filter to only available channels
        valid_chs = [ch for ch in ch_names if ch in available_chs]
        if not valid_chs:
            raise ValueError(f"No valid channels found for extraction: {ch_names}")
        ch_names = valid_chs

    # Find frequency indices corresponding to the band
    freqs = tfr.freqs
    freq_mask = (freqs >= freq_band[0]) & (freqs <= freq_band[1])
    if not np.any(freq_mask):
        raise ValueError(f"No frequencies found in range {freq_band}. Available: {freqs}")
    freq_indices = np.where(freq_mask)[0]

    # Find time indices corresponding to the window
    times = tfr.times
    time_mask = (times >= time_window[0]) & (times <= time_window[1])
    if not np.any(time_mask):
        raise ValueError(f"No time points found in range {time_window}. Available: {times}")
    time_indices = np.where(time_mask)[0]

    # Extract channel indices
    ch_indices = [epochs.ch_names.index(ch) for ch in ch_names]

    # Get power data: shape (n_epochs, n_channels, n_freqs, n_times)
    # tfr.data is usually (n_epochs, n_channels, n_freqs, n_times)
    power_data = tfr.data

    # Squeeze dimensions to get mean over freqs, times, and selected channels
    # We want mean over freqs, times, and channels -> result per epoch
    subset = power_data[:, ch_indices[:, None, None, None], freq_indices[None, :, None, None], time_indices[None, None, :, None]]
    
    # Mean over channels (axis 1), freqs (axis 2), times (axis 3)
    mean_power = subset.mean(axis=(1, 2, 3))
    
    return mean_power.reshape(-1, 1)

def run_extraction(
    epochs_path: str,
    output_path: str,
    freqs: np.ndarray,
    n_cycles: List[float],
    baseline: Tuple[float, float],
    alpha_band: Tuple[float, float] = (8.0, 12.0),
    beta_band: Tuple[float, float] = (13.0, 30.0),
    parietal_chs: List[str] = ['P3', 'Pz', 'P4'],
    frontal_chs: List[str] = ['F3', 'Fz', 'F4'],
    time_window: Tuple[float, float] = (0.0, 1.0)
) -> Dict[str, Any]:
    """
    Run the full feature extraction pipeline.
    
    This function:
    1. Loads epochs.
    2. Computes TFR.
    3. Normalizes baseline.
    4. Extracts mean alpha power for parietal electrodes.
    5. Extracts mean beta power for frontal electrodes (T021).
    6. Saves the feature matrix.
    
    Args:
        epochs_path: Path to input epochs file.
        output_path: Path to save feature matrix.
        freqs: Frequencies for TFR.
        n_cycles: Cycles for TFR.
        baseline: Baseline window for normalization.
        alpha_band: Frequency range for alpha.
        beta_band: Frequency range for beta.
        parietal_chs: Channel names for alpha extraction.
        frontal_chs: Channel names for beta extraction.
        time_window: Time window for averaging power.
        
    Returns:
        Dictionary with extraction results and metadata.
    """
    logger.info("Starting feature extraction pipeline")
    
    # 1. Load Epochs
    epochs = load_epochs(epochs_path)
    
    # 2. Compute TFR
    tfr = compute_time_frequency(epochs, freqs, n_cycles)
    
    # 3. Baseline Normalize
    tfr_norm = baseline_normalize(tfr, baseline, mode='logratio')
    
    # 4. Extract Alpha Power (Parietal) - T020
    logger.info(f"Extracting alpha power ({alpha_band[0]}-{alpha_band[1]}Hz) for parietal channels: {parietal_chs}")
    alpha_power = extract_mean_power(
        epochs, tfr_norm, alpha_band, parietal_chs, time_window
    )
    
    # 5. Extract Beta Power (Frontal) - T021
    logger.info(f"Extracting beta power ({beta_band[0]}-{beta_band[1]}Hz) for frontal channels: {frontal_chs}")
    beta_power = extract_mean_power(
        epochs, tfr_norm, beta_band, frontal_chs, time_window
    )
    
    # 6. Construct Feature Matrix
    n_epochs = epochs.get_data().shape[0]
    # Get condition labels from epochs
    # Assuming epochs have a 'condition' or similar annotation, or we infer from event_id
    # For robustness, we check metadata or events
    conditions = np.array([str(epochs.events[i, 2]) for i in range(n_epochs)])
    # If conditions are numeric IDs, map them to labels if possible, otherwise keep as is
    # A common convention is 1=active, 0=passive or similar. 
    # We will store the raw event codes as 'condition' for now, or try to map.
    # If epochs.event_id is present:
    if epochs.event_id:
        # Invert mapping: code -> label
        inv_map = {v: k for k, v in epochs.event_id.items()}
        conditions = np.array([inv_map.get(int(c), str(c)) for c in conditions])
    
    feature_matrix = np.hstack([
        np.arange(n_epochs).reshape(-1, 1), # epoch_id
        np.array([conditions]).T,           # condition (string or code)
        alpha_power,                        # P_alpha (mean of P3, Pz, P4)
        beta_power                          # F_beta (mean of F3, Fz, F4)
    ])
    
    # 7. Save to CSV
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Define headers
    headers = ['epoch_id', 'condition', 'P_alpha', 'F_beta']
    
    # If we need specific electrode names as per T023 schema, we might need to extract individually
    # T023 schema: 'P3_alpha', 'Pz_alpha', 'P4_alpha', 'F3_beta', 'Fz_beta', 'F4_beta'
    # The current run_extraction aggregates. Let's adjust to match T023 schema if required.
    # However, T021 specifically asks for "mean beta power ... for frontal electrodes".
    # The T023 task description says: "Schema: 'epoch_id', 'condition', 'P_alpha', 'Pz_alpha', 'P4_alpha', 'F3_beta', 'Fz_beta', 'F4_beta'".
    # This implies we need per-electrode extraction, not just mean.
    # Let's refactor to extract per-electrode to satisfy T023/T021 strictly.
    
    # Re-extract per electrode for T021 compliance and T023 schema
    alpha_features = []
    beta_features = []
    
    for ch in parietal_chs:
        if ch in epochs.ch_names:
            val = extract_mean_power(epochs, tfr_norm, alpha_band, [ch], time_window)
            alpha_features.append(val)
        else:
            logger.warning(f"Channel {ch} not found, appending NaN")
            alpha_features.append(np.full((n_epochs, 1), np.nan))
    
    for ch in frontal_chs:
        if ch in epochs.ch_names:
            val = extract_mean_power(epochs, tfr_norm, beta_band, [ch], time_window)
            beta_features.append(val)
        else:
            logger.warning(f"Channel {ch} not found, appending NaN")
            beta_features.append(np.full((n_epochs, 1), np.nan))
    
    # Combine: epoch_id, condition, P3_alpha, Pz_alpha, P4_alpha, F3_beta, Fz_beta, F4_beta
    feature_parts = [
        np.arange(n_epochs).reshape(-1, 1),
        np.array([[c] for c in conditions]).astype(object), # Keep as object for mixed types if needed
    ]
    feature_parts.extend(alpha_features)
    feature_parts.extend(beta_features)
    
    final_matrix = np.hstack(feature_parts)
    
    # Save
    import csv
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers) # Wait, headers need to match columns
        # Correct headers for the new structure
        col_headers = ['epoch_id', 'condition'] + [f'{ch}_alpha' for ch in parietal_chs] + [f'{ch}_beta' for ch in frontal_chs]
        writer.writerow(col_headers)
        for row in final_matrix:
            writer.writerow(row)
    
    logger.info(f"Feature matrix saved to {output_file}")
    
    return {
        "n_epochs": n_epochs,
        "features": col_headers,
        "alpha_band": alpha_band,
        "beta_band": beta_band,
        "parietal_channels": parietal_chs,
        "frontal_channels": frontal_chs,
        "output_path": str(output_file)
    }

def main():
    """Main entry point for feature extraction."""
    config = get_config()
    paths = config.get('paths', {})
    epochs_path = paths.get('epochs_cleaned', 'data/processed/epochs_cleaned.fif')
    output_path = paths.get('features_matrix', 'data/processed/features_matrix.csv')
    
    # Define parameters
    freqs = np.arange(1, 40, 1) # 1 to 39 Hz
    n_cycles = freqs / 2.0 # Standard Morlet setting
    baseline = (-1.0, 0.0)
    time_window = (0.0, 1.0)
    
    # Run
    try:
        result = run_extraction(
            epochs_path=epochs_path,
            output_path=output_path,
            freqs=freqs,
            n_cycles=n_cycles,
            baseline=baseline,
            time_window=time_window
        )
        print(f"Extraction complete. Output: {result['output_path']}")
    except Exception as e:
        logger.error(f"Feature extraction failed: {e}")
        raise

if __name__ == "__main__":
    main()