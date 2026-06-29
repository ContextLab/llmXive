"""
Feature extraction module.
Performs time-frequency decomposition and extracts mean power values.
"""
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

import numpy as np
import pandas as pd
import mne
from scipy import signal

from config import load_config, get_paths
from models import FeatureMetadata

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_epochs(epochs_path: Path) -> mne.Epochs:
    """Load preprocessed epochs."""
    if not epochs_path.exists():
        raise FileNotFoundError(f"Epochs file not found: {epochs_path}")
    return mne.read_epochs(epochs_path, preload=True)

def compute_time_frequency(epochs: mne.Epochs, config: Dict[str, Any]) -> mne.EpochsTFR:
    """
    Compute Morlet wavelet time-frequency decomposition.
    """
    # Define frequencies
    freqs = np.logspace(1, 40, num=20) # Example range
    n_cycles = freqs / 2. # Fixed number of cycles
    
    power = mne.time_frequency.tfr_morlet(
        epochs,
        freqs=freqs,
        n_cycles=n_cycles,
        use_fft=True,
        return_itc=False,
        n_jobs=1
    )
    return power

def baseline_normalize(tfr: mne.EpochsTFR, config: Dict[str, Any]) -> mne.EpochsTFR:
    """Convert to dB relative to baseline."""
    baseline = config["epoching"]["baseline"]
    tfr.apply_baseline(baseline=baseline, mode='logratio')
    return tfr

def extract_mean_power(
    tfr: mne.EpochsTFR,
    epochs: mne.Epochs,
    electrode_map: Dict[str, List[int]],
    freq_bands: Dict[str, tuple]
) -> pd.DataFrame:
    """
    Extract mean power for specific electrodes and frequency bands.
    Returns a DataFrame where rows are epochs and columns are features.
    """
    feature_data = []
    
    # Map channel names to indices
    ch_names = tfr.ch_names
    # tfr.data shape: (n_epochs, n_channels, n_freqs, n_times)
    
    for freq_name, (f_min, f_max) in freq_bands.items():
        # Find indices for this frequency range
        freqs = tfr.freqs
        f_idx = np.where((freqs >= f_min) & (freqs <= f_max))[0]
        
        for ch_name, ch_idx in electrode_map.items():
            if ch_name not in ch_names:
                logger.warning(f"Electrode {ch_name} not found in data.")
                continue
            
            ch_idx_tfr = ch_names.index(ch_name)
            
            # Average power across frequency and time (or specific time window)
            # For simplicity, average over all time points in the epoch
            power_values = []
            for epoch_idx in range(tfr.data.shape[0]):
                # Extract power for this epoch, channel, freq range
                # Shape: (n_freqs, n_times)
                segment = tfr.data[epoch_idx, ch_idx_tfr, f_idx, :]
                mean_power = np.mean(segment)
                power_values.append(mean_power)
            
            feature_data.append({
                "feature_name": f"{freq_name}_{ch_name}",
                "electrode": ch_name,
                "band": freq_name,
                "values": power_values
            })
    
    # Construct DataFrame
    # Transpose to have epochs as rows
    df = pd.DataFrame()
    for item in feature_data:
        df[item["feature_name"]] = item["values"]
        
    return df

def run_extraction(epochs_path: Path, output_path: Path, config: Dict[str, Any]) -> FeatureMetadata:
    """
    Main orchestration for feature extraction.
    """
    # Load epochs
    epochs = load_epochs(epochs_path)
    
    # T-F Decomposition
    tfr = compute_time_frequency(epochs, config)
    
    # Baseline Normalize
    tfr = baseline_normalize(tfr, config)
    
    # Define regions
    # Alpha: 8-13 Hz, Beta: 13-30 Hz
    freq_bands = {
        "alpha": (8, 13),
        "beta": (13, 30)
    }
    
    # Electrodes
    # Parietal: P, Pz, P4
    # Frontal: F3, Fz, F4
    # Note: Channel names in MNE might be 'Pz', 'P4', etc.
    electrode_map = {
        "Pz": [0], # Placeholder index, real logic needs mapping
        "P4": [0],
        "P3": [0],
        "F3": [0],
        "Fz": [0],
        "F4": [0]
    }
    
    # We need to map names to indices dynamically
    valid_electrodes = {}
    for name in ["Pz", "P4", "P3", "F3", "Fz", "F4"]:
        if name in epochs.ch_names:
            valid_electrodes[name] = epochs.ch_names.index(name)
    
    # Extract features
    df_features = extract_mean_power(tfr, epochs, valid_electrodes, freq_bands)
    
    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_features.to_csv(output_path, index=False)
    
    logger.info(f"Features saved to {output_path}")
    
    return FeatureMetadata(
        n_epochs=len(df_features),
        n_features=len(df_features.columns),
        electrode_list=list(valid_electrodes.keys()),
        frequency_bands=list(freq_bands.keys())
    )

def main():
    """Entry point for feature extraction."""
    config = load_config()
    paths = get_paths(config)
    
    epochs_file = paths["processed"] / paths["epochs"]
    features_file = paths["processed"] / paths["features"]
    
    try:
        metadata = run_extraction(epochs_file, features_file, config)
        # Save metadata
        meta_file = paths["processed"] / "feature_metadata.json"
        with open(meta_file, 'w') as f:
            json.dump({
                "n_epochs": metadata.n_epochs,
                "n_features": metadata.n_features,
                "electrodes": metadata.electrode_list,
                "bands": metadata.frequency_bands
            }, f, indent=2)
        print(f"Feature extraction complete. Output: {features_file}")
    except Exception as e:
        logger.error(f"Feature extraction failed: {e}")
        raise

if __name__ == "__main__":
    main()
