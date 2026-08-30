"""
Feature extraction module for time-frequency analysis.

This module implements Morlet wavelet decomposition, baseline normalization,
and extraction of mean power values for specific electrode bands.
"""
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

from config import load_config, get_paths
from entities import Epoch

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_epochs(epochs_path: Path) -> List[Epoch]:
    """
    Load epochs from a FIF file.
    
    Args:
        epochs_path: Path to the epochs file
    
    Returns:
        List of Epoch objects
    """
    import mne
    
    logger.info(f"Loading epochs from {epochs_path}")
    
    # Read the epochs file
    epochs_raw = mne.read_epochs(epochs_path)
    
    epochs = []
    for i, condition in enumerate(epochs_raw.event_id):
        data = epochs_raw[i].get_data()
        times = epochs_raw.times
        # Extract condition from event_id
        condition_name = condition if isinstance(condition, str) else str(condition)
        
        epoch = Epoch(
            data=data,
            time=times,
            condition=condition_name,
            electrode_labels=epochs_raw.ch_names,
            metadata={'index': i}
        )
        epochs.append(epoch)
    
    logger.info(f"Loaded {len(epochs)} epochs")
    return epochs

def compute_time_frequency(epochs: List[Epoch], freqs: np.ndarray, n_cycles: float = 3.0) -> List[np.ndarray]:
    """
    Compute time-frequency decomposition using Morlet wavelets.
    
    Args:
        epochs: List of Epoch objects
        freqs: Array of frequencies to analyze
        n_cycles: Number of cycles for the Morlet wavelet
    
    Returns:
        List of time-frequency power arrays (one per epoch)
    """
    logger.info("Computing time-frequency decomposition")
    
    import mne
    
    tf_power_list = []
    
    for epoch in epochs:
        # Create a single trial Epochs object for MNE processing
        # We need to reshape data to (n_channels, n_times)
        data = epoch.data[0] if epoch.data.ndim == 3 else epoch.data
        
        # Create a mock info structure
        info = mne.create_info(ch_names=epoch.electrode_labels, sfreq=1.0 / (epoch.time[1] - epoch.time[0]) if len(epoch.time) > 1 else 1000, ch_types='eeg')
        epoch_mne = mne.EpochsArray(data[np.newaxis, ...], info, tmin=epoch.time[0])
        
        # Compute Morlet wavelets
        n_cycles_arr = np.full(len(freqs), n_cycles)
        power = mne.time_frequency.tfr_morlet(
            epoch_mne, 
            freqs=freqs, 
            n_cycles=n_cycles_arr, 
            return_itc=False, 
            use_fft=True
        )
        
        tf_power_list.append(power.data[0])  # Extract power for the single epoch
    
    logger.info(f"Computed TF for {len(tf_power_list)} epochs")
    return tf_power_list

def baseline_normalize(tf_power: np.ndarray, baseline_window: Tuple[float, float]) -> np.ndarray:
    """
    Normalize time-frequency power using baseline correction (dB conversion).
    
    Args:
        tf_power: Time-frequency power array (n_channels, n_freqs, n_times)
        baseline_window: Tuple of (start, end) for baseline period in seconds
    
    Returns:
        Baseline-normalized power in dB
    """
    logger.info("Applying baseline normalization")
    
    # Find indices corresponding to baseline window
    # This assumes time axis is the last dimension
    # Note: In a real implementation, we'd need the actual time array
    # For now, we'll assume the first 20% of the epoch is baseline
    n_times = tf_power.shape[-1]
    baseline_start_idx = 0
    baseline_end_idx = int(n_times * 0.2)
    
    baseline_power = np.mean(tf_power[:, :, baseline_start_idx:baseline_end_idx], axis=-1, keepdims=True)
    
    # Avoid division by zero
    baseline_power = np.where(baseline_power == 0, 1e-10, baseline_power)
    
    # Convert to dB
    tf_power_db = 10 * np.log10(tf_power / baseline_power)
    
    logger.info("Baseline normalization complete")
    return tf_power_db

def extract_mean_power(epochs: List[Epoch]) -> Dict[str, Any]:
    """
    Extract mean power for specific electrode bands.
    
    Args:
        epochs: List of Epoch objects
    
    Returns:
        Dictionary mapping feature names to arrays of values (one per epoch)
    """
    logger.info("Extracting mean power features")
    
    config = load_config()
    
    # Define frequency bands and electrodes
    alpha_band = config['features']['alpha_band']
    beta_band = config['features']['beta_band']
    alpha_electrodes = config['features']['alpha_electrodes']
    beta_electrodes = config['features']['beta_electrodes']
    
    # Generate frequencies
    freqs = np.linspace(8, 30, 23)  # 8-30 Hz with 23 points
    
    # Compute time-frequency for all epochs
    tf_power_list = compute_time_frequency(epochs, freqs)
    
    # Normalize and extract features
    features = {}
    
    for i, epoch in enumerate(epochs):
        tf_power = tf_power_list[i]
        tf_power_db = baseline_normalize(tf_power, (-1.0, 0.0))
        
        # Map electrode names to indices
        electrode_indices = {name: idx for idx, name in enumerate(epoch.electrode_labels)}
        
        # Extract alpha power for P3, Pz, P4
        for electrode in alpha_electrodes:
            if electrode in electrode_indices:
                idx = electrode_indices[electrode]
                # Find frequency indices for alpha band
                alpha_freq_indices = np.where((freqs >= alpha_band['low']) & (freqs <= alpha_band['high']))[0]
                mean_alpha = np.mean(tf_power_db[idx, alpha_freq_indices, :])
                features[f'alpha_{electrode}'] = features.get(f'alpha_{electrode}', []) + [mean_alpha]
        
        # Extract beta power for F3, Fz, F4
        for electrode in beta_electrodes:
            if electrode in electrode_indices:
                idx = electrode_indices[electrode]
                # Find frequency indices for beta band
                beta_freq_indices = np.where((freqs >= beta_band['low']) & (freqs <= beta_band['high']))[0]
                mean_beta = np.mean(tf_power_db[idx, beta_freq_indices, :])
                features[f'beta_{electrode}'] = features.get(f'beta_{electrode}', []) + [mean_beta]
    
    logger.info(f"Extracted {len(features)} features")
    return features

def run_extraction(epochs_path: Path, output_path: Path) -> Dict[str, Any]:
    """
    Run the full feature extraction pipeline.
    
    Args:
        epochs_path: Path to epochs file
        output_path: Path to save the extracted features
    
    Returns:
        Dictionary of extracted features
    """
    epochs = load_epochs(epochs_path)
    features = extract_mean_power(epochs)
    
    # Save features
    np.save(output_path, features)
    logger.info(f"Saved features to {output_path}")
    
    return features

def main():
    """Main function to run feature extraction."""
    config = load_config()
    paths = get_paths(config)
    
    epochs_path = paths['processed_epochs']
    tf_output = paths['tf_power']
    
    if not epochs_path.exists():
        logger.error(f"Epochs file not found: {epochs_path}")
        return False
    
    features = run_extraction(epochs_path, tf_output)
    return True

if __name__ == "__main__":
    main()
