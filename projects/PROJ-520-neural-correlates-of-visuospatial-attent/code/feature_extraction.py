import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import mne

from logger import get_logger
from config import get_config
from preprocessing import SampleSizeError

# Ensure imports from sibling modules exist in the public API surface
# The API surface lists these names for feature_extraction.py:
# load_epochs, compute_time_frequency, baseline_normalize, extract_mean_power, run_extraction, main

def load_epochs(epochs_path: str) -> mne.Epochs:
    """Load preprocessed epochs from a .fif file."""
    logger = get_logger(__name__)
    path = Path(epochs_path)
    if not path.exists():
        raise FileNotFoundError(f"Epochs file not found: {epochs_path}")
    
    logger.info(f"Loading epochs from {epochs_path}")
    epochs = mne.read_epochs(str(path))
    logger.info(f"Loaded {len(epochs)} epochs")
    return epochs

def compute_time_frequency(epochs: mne.Epochs, freqs: List[float], n_cycles: float = 3.0) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Compute Morlet wavelet time-frequency decomposition.
    
    Args:
        epochs: MNE Epochs object
        freqs: List of frequencies to compute
        n_cycles: Number of cycles for Morlet wavelets
        
    Returns:
        Tuple of (tf_power, freqs, times)
    """
    logger = get_logger(__name__)
    logger.info(f"Computing time-frequency decomposition for {len(freqs)} frequencies")
    
    # Use mne.time_frequency.tfr_morlet
    tf_power = mne.time_frequency.tfr_morlet(
        epochs, 
        freqs=freqs, 
        n_cycles=n_cycles, 
        use_fft=True, 
        return_itc=False, 
        decim=1
    )
    
    # tf_power.data shape: (n_epochs, n_channels, n_freqs, n_times)
    # We return the power array
    return tf_power.data, np.array(freqs), tf_power.times

def baseline_normalize(tf_power: np.ndarray, baseline: Tuple[float, float], mode: str = 'db') -> np.ndarray:
    """
    Apply baseline normalization to time-frequency power.
    
    Args:
        tf_power: Time-frequency power array (n_epochs, n_channels, n_freqs, n_times)
        baseline: Tuple of (start, end) in seconds for baseline period
        mode: Normalization mode ('db' for decibels)
        
    Returns:
        Normalized power array
    """
    logger = get_logger(__name__)
    logger.info(f"Applying baseline normalization: mode={mode}, baseline={baseline}")
    
    # Create a dummy MNE EpochsArray to use mne's baseline functionality
    # Or implement manually
    # Manual implementation for db mode:
    # 1. Identify baseline time indices
    # 2. Compute mean baseline power per epoch, channel, freq
    # 3. Convert to dB: 10 * log10(power / baseline_mean)
    
    times = np.arange(tf_power.shape[-1])  # We need actual times, but we don't have them here
    # This function assumes we have access to times or we pass them
    # For now, let's assume we get times from the caller or use indices
    # Better: pass times as well or compute from epoch info
    
    # Simplified: assume we have times passed or we use a standard approach
    # Let's re-implement to be more robust
    raise NotImplementedError("Baseline normalization requires times array; refactor to accept times")

def baseline_normalize_with_times(tf_power: np.ndarray, times: np.ndarray, baseline: Tuple[float, float], mode: str = 'db') -> np.ndarray:
    """
    Apply baseline normalization to time-frequency power with explicit times.
    
    Args:
        tf_power: Time-frequency power array (n_epochs, n_channels, n_freqs, n_times)
        times: Array of time points in seconds
        baseline: Tuple of (start, end) in seconds for baseline period
        mode: Normalization mode ('db' for decibels)
        
    Returns:
        Normalized power array (same shape as input)
    """
    logger = get_logger(__name__)
    logger.info(f"Applying baseline normalization: mode={mode}, baseline={baseline}")
    
    # Find baseline time indices
    baseline_mask = (times >= baseline[0]) & (times <= baseline[1])
    baseline_times = times[baseline_mask]
    
    if len(baseline_times) == 0:
        raise ValueError(f"No time points in baseline range {baseline}")
    
    # Compute mean baseline power for each epoch, channel, frequency
    baseline_power = tf_power[..., baseline_mask].mean(axis=-1, keepdims=True)
    
    # Avoid division by zero
    baseline_power = np.where(baseline_power == 0, 1e-10, baseline_power)
    
    if mode == 'db':
        # Convert to decibels: 10 * log10(power / baseline)
        normalized = 10 * np.log10(tf_power / baseline_power)
    elif mode == 'ratio':
        normalized = tf_power / baseline_power
    else:
        raise ValueError(f"Unknown normalization mode: {mode}")
    
    logger.info(f"Baseline normalization complete. Output range: [{normalized.min():.2f}, {normalized.max():.2f}]")
    return normalized

def extract_mean_power(normalized_tf_power: np.ndarray, 
                      times: np.ndarray, 
                      freqs: np.ndarray, 
                      ch_names: List[str],
                      electrode_band_map: Dict[str, Tuple[str, float, float]]) -> Dict[str, np.ndarray]:
    """
    Extract mean power for specific electrode-band combinations.
    
    Args:
        normalized_tf_power: Normalized time-frequency power (n_epochs, n_channels, n_freqs, n_times)
        times: Time points in seconds
        freqs: Frequencies in Hz
        ch_names: List of channel names
        electrode_band_map: Dict mapping electrode name to (band_name, freq_low, freq_high)
                           Example: {'P3': ('alpha', 8.0, 12.0), 'F3': ('beta', 13.0, 30.0)}
                           
    Returns:
        Dict mapping electrode_band_key to mean power array (n_epochs,)
    """
    logger = get_logger(__name__)
    logger.info(f"Extracting mean power for {len(electrode_band_map)} electrode-band combinations")
    
    results = {}
    
    for electrode, (band, freq_low, freq_high) in electrode_band_map.items():
        # Find channel index
        if electrode not in ch_names:
            logger.warning(f"Electrode {electrode} not found in channels. Skipping.")
            continue
        
        ch_idx = ch_names.index(electrode)
        
        # Find frequency indices for the band
        freq_mask = (freqs >= freq_low) & (freqs <= freq_high)
        freq_indices = np.where(freq_mask)[0]
        
        if len(freq_indices) == 0:
            logger.warning(f"No frequencies found for band {band} ({freq_low}-{freq_high} Hz) for {electrode}. Skipping.")
            continue
        
        # Find time indices for the analysis window (e.g., post-stimulus 0.0 to 2.0s)
        # Assuming we want the entire epoch or a specific window
        # For visuospatial attention, we might look at 0.5-2.0s post-stimulus
        time_window = (0.0, 2.0)  # Default to full epoch or adjust
        time_mask = (times >= time_window[0]) & (times <= time_window[1])
        time_indices = np.where(time_mask)[0]
        
        if len(time_indices) == 0:
            logger.warning(f"No time points found in window {time_window}. Skipping.")
            continue
        
        # Extract power for this electrode and frequency band
        # Shape: (n_epochs, n_freqs, n_times)
        power_subset = normalized_tf_power[:, ch_idx, freq_indices, :][:, :, time_indices]
        
        # Compute mean across frequencies and time
        mean_power = power_subset.mean(axis=(1, 2))  # Average over freq and time, keep epochs
        
        key = f"{electrode}_{band}"
        results[key] = mean_power
        logger.info(f"Extracted {key}: shape={mean_power.shape}, mean={mean_power.mean():.4f}, std={mean_power.std():.4f}")
    
    return results

def run_extraction(epochs_path: str, 
                  output_path: str,
                  freqs: List[float] = None,
                  baseline: Tuple[float, float] = (-0.2, 0.0),
                  electrode_band_map: Dict[str, Tuple[str, float, float]] = None) -> Dict[str, Any]:
    """
    Run the full feature extraction pipeline.
    
    Args:
        epochs_path: Path to preprocessed epochs .fif file
        output_path: Path to save feature matrix CSV
        freqs: List of frequencies for TFR (default: alpha and beta ranges)
        baseline: Baseline period for normalization
        electrode_band_map: Mapping of electrodes to bands and frequencies
        
    Returns:
        Dict with extraction results and metadata
    """
    logger = get_logger(__name__)
    logger.info("Starting feature extraction pipeline")
    
    # Load epochs
    epochs = load_epochs(epochs_path)
    ch_names = epochs.ch_names
    
    # Default frequencies: alpha (8-12 Hz) and beta (13-30 Hz)
    if freqs is None:
        freqs = list(np.arange(4.0, 35.0, 1.0))
    
    # Default electrode-band map for parietal alpha and frontal beta
    if electrode_band_map is None:
        electrode_band_map = {
            'P3': ('alpha', 8.0, 12.0),
            'Pz': ('alpha', 8.0, 12.0),
            'P4': ('alpha', 8.0, 12.0),
            'F3': ('beta', 13.0, 30.0),
            'Fz': ('beta', 13.0, 30.0),
            'F4': ('beta', 13.0, 30.0)
        }
    
    # Compute time-frequency decomposition
    tf_power, freqs_array, times = compute_time_frequency(epochs, freqs)
    
    # Baseline normalize
    normalized_tf_power = baseline_normalize_with_times(tf_power, times, baseline)
    
    # Extract mean power
    power_results = extract_mean_power(normalized_tf_power, times, freqs_array, ch_names, electrode_band_map)
    
    # Save results
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save individual power arrays as npy (for debugging/inspection)
    for key, values in power_results.items():
        npy_path = output_dir / f"{key}_power.npy"
        np.save(str(npy_path), values)
        logger.info(f"Saved {key} power to {npy_path}")
    
    # Create feature matrix DataFrame
    import pandas as pd
    n_epochs = len(epochs)
    feature_dict = {
        'epoch_id': np.arange(n_epochs),
        'condition': epochs.events[:, 2]  # Assuming condition is in the third column of events
    }
    feature_dict.update({key: values for key, values in power_results.items()})
    
    df = pd.DataFrame(feature_dict)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved feature matrix to {output_path}")
    
    # Return metadata
    metadata = {
        'n_epochs': n_epochs,
        'n_channels': len(ch_names),
        'freqs': freqs_array.tolist(),
        'baseline': baseline,
        'electrode_band_map': electrode_band_map,
        'output_file': output_path,
        'features_extracted': list(power_results.keys())
    }
    
    return metadata

def main():
    """Main entry point for feature extraction."""
    logger = get_logger(__name__)
    config = get_config()
    
    epochs_path = config.get('OUTPUT_PATH', 'data/processed') + '/epochs_cleaned.fif'
    output_path = config.get('OUTPUT_PATH', 'data/processed') + '/features_matrix.csv'
    
    # Default parameters
    freqs = list(np.arange(4.0, 35.0, 1.0))
    baseline = (-0.2, 0.0)
    electrode_band_map = {
        'P3': ('alpha', 8.0, 12.0),
        'Pz': ('alpha', 8.0, 12.0),
        'P4': ('alpha', 8.0, 12.0),
        'F3': ('beta', 13.0, 30.0),
        'Fz': ('beta', 13.0, 30.0),
        'F4': ('beta', 13.0, 30.0)
    }
    
    try:
        metadata = run_extraction(
            epochs_path=epochs_path,
            output_path=output_path,
            freqs=freqs,
            baseline=baseline,
            electrode_band_map=electrode_band_map
        )
        logger.info(f"Feature extraction completed successfully. Output: {output_path}")
        return metadata
    except Exception as e:
        logger.error(f"Feature extraction failed: {e}")
        raise

if __name__ == "__main__":
    main()