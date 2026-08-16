import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

import mne
from scipy.signal import butter, filtfilt

from config import get_paths, get_seed
from logging_config import get_pipeline_logger, log_stage_start, log_stage_end

logger = get_pipeline_logger(__name__)

# Constants for frequency bands (Hz)
ALPHA_BAND = (8, 13)
BETA_BAND = (13, 30)

def load_epochs(epochs_path: Path) -> mne.Epochs:
    """Load preprocessed epochs from a FIF file.
    
    Args:
        epochs_path: Path to the epochs_cleaned.fif file.
        
    Returns:
        mne.Epochs object containing the preprocessed data.
        
    Raises:
        FileNotFoundError: If the epochs file does not exist.
        RuntimeError: If the file cannot be loaded or is invalid.
    """
    if not epochs_path.exists():
        raise FileNotFoundError(f"Epochs file not found: {epochs_path}")
    
    try:
        epochs = mne.read_epochs(epochs_path, preload=True)
        logger.info(f"Loaded {len(epochs)} epochs from {epochs_path}")
        return epochs
    except Exception as e:
        logger.error(f"Failed to load epochs: {e}")
        raise RuntimeError(f"Could not load epochs from {epochs_path}: {e}")

def compute_time_frequency(
    epochs: mne.Epochs,
    freqs: np.ndarray,
    n_cycles: List[float],
    mode: str = 'average',
    use_fft: bool = True
) -> mne.TimeFrequency:
    """Compute Morlet wavelet time-frequency decomposition.
    
    Args:
        epochs: Preprocessed epochs object.
        freqs: Array of frequencies to compute.
        n_cycles: Number of cycles for each frequency.
        mode: 'average' or 'single'.
        use_fft: Whether to use FFT-based convolution.
        
    Returns:
        mne.TimeFrequency object containing the time-frequency representation.
    """
    logger.info(f"Computing time-frequency decomposition for {len(freqs)} frequencies")
    
    try:
        tfr = mne.time_frequency.tfr_morlet(
            epochs, 
            freqs=freqs, 
            n_cycles=n_cycles, 
            use_fft=use_fft,
            return_average=(mode == 'average'),
            decim=1
        )
        logger.info(f"Time-frequency decomposition complete. Shape: {tfr.data.shape}")
        return tfr
    except Exception as e:
        logger.error(f"Time-frequency computation failed: {e}")
        raise

def baseline_normalize(
    tfr: mne.TimeFrequency,
    baseline: Tuple[float, float],
    mode: str = 'db'
) -> mne.TimeFrequency:
    """Apply baseline normalization to time-frequency data.
    
    Args:
        tfr: TimeFrequency object to normalize.
        baseline: Tuple of (start, end) time in seconds for baseline period.
        mode: Normalization mode ('db' for decibels).
        
    Returns:
        Normalized TimeFrequency object.
    """
    logger.info(f"Applying baseline normalization ({mode}) for period {baseline}")
    
    try:
        tfr.apply_baseline(baseline=baseline, mode=mode)
        logger.info("Baseline normalization complete")
        return tfr
    except Exception as e:
        logger.error(f"Baseline normalization failed: {e}")
        raise

def extract_mean_power(
    tfr: mne.TimeFrequency,
    electrodes: List[str],
    freq_band: Tuple[float, float],
    time_window: Optional[Tuple[float, float]] = None
) -> np.ndarray:
    """Extract mean power for specific electrodes and frequency band.
    
    Args:
        tfr: Normalized TimeFrequency object.
        electrodes: List of electrode names to extract.
        freq_band: Tuple of (min_freq, max_freq) in Hz.
        time_window: Optional tuple of (start, end) time in seconds. 
                     If None, uses entire time range.
                     
    Returns:
        2D numpy array of shape (n_epochs, n_features) containing mean power.
        
    Raises:
        ValueError: If electrodes are not found in the data.
    """
    # Find indices for the frequency band
    freqs = tfr.freqs
    freq_mask = (freqs >= freq_band[0]) & (freqs <= freq_band[1])
    freq_indices = np.where(freq_mask)[0]
    
    if len(freq_indices) == 0:
        raise ValueError(f"No frequencies found in band {freq_band}")
    
    # Find indices for the electrodes
    try:
        ch_names = tfr.ch_names
        ch_indices = [ch_names.index(ch) for ch in electrodes if ch in ch_names]
        
        if len(ch_indices) != len(electrodes):
            missing = set(electrodes) - set(ch_names)
            logger.warning(f"Missing electrodes: {missing}. Using available: {electrodes}")
            electrodes = [ch for ch in electrodes if ch in ch_names]
            ch_indices = [ch_names.index(ch) for ch in electrodes]
            
    except (ValueError, AttributeError) as e:
        logger.error(f"Failed to locate electrodes: {e}")
        raise ValueError(f"Could not find electrodes {electrodes} in data")
    
    # Find indices for the time window
    times = tfr.times
    if time_window is not None:
        time_mask = (times >= time_window[0]) & (times <= time_window[1])
        time_indices = np.where(time_mask)[0]
        
        if len(time_indices) == 0:
            raise ValueError(f"No time points found in window {time_window}")
    else:
        time_indices = np.arange(len(times))
    
    # Extract and compute mean power
    # tfr.data shape: (n_epochs, n_channels, n_freqs, n_times)
    power_data = tfr.data[:, ch_indices, :, :]
    
    # Select relevant frequency and time indices
    power_subset = power_data[:, :, freq_indices, :][:, :, :, time_indices]
    
    # Compute mean across frequency and time dimensions
    mean_power = np.mean(power_subset, axis=(2, 3))
    
    logger.info(f"Extracted mean power for {len(electrodes)} electrodes, "
               f"shape: {mean_power.shape}")
    
    return mean_power

def run_extraction(
    epochs_path: Path,
    output_path: Path,
    electrodes_alpha: List[str],
    electrodes_beta: List[str],
    freq_band_alpha: Tuple[float, float],
    freq_band_beta: Tuple[float, float],
    time_window: Optional[Tuple[float, float]] = None,
    baseline: Tuple[float, float] = (-0.2, 0.0)
) -> Dict[str, Any]:
    """Run the full feature extraction pipeline.
    
    Args:
        epochs_path: Path to input epochs file.
        output_path: Path to save output features.
        electrodes_alpha: List of electrodes for alpha band.
        electrodes_beta: List of electrodes for beta band.
        freq_band_alpha: Alpha frequency band (Hz).
        freq_band_beta: Beta frequency band (Hz).
        time_window: Optional time window for feature extraction.
        baseline: Baseline period for normalization.
        
    Returns:
        Dictionary containing extraction results and metadata.
    """
    log_stage_start(logger, "Feature Extraction")
    
    try:
        # Load epochs
        epochs = load_epochs(epochs_path)
        
        # Define frequencies for wavelet transform
        # Generate frequencies from 1 to 40 Hz with logarithmic spacing
        n_freqs = 30
        freqs = np.linspace(1, 40, n_freqs)
        n_cycles = freqs / 2.0  # Standard Morlet configuration
        
        # Compute time-frequency representation
        tfr = compute_time_frequency(epochs, freqs, n_cycles, mode='average', use_fft=True)
        
        # Baseline normalize
        tfr = baseline_normalize(tfr, baseline=baseline, mode='db')
        
        # Extract alpha power
        alpha_power = extract_mean_power(
            tfr, 
            electrodes_alpha, 
            freq_band_alpha, 
            time_window=time_window
        )
        
        # Extract beta power
        beta_power = extract_mean_power(
            tfr, 
            electrodes_beta, 
            freq_band_beta, 
            time_window=time_window
        )
        
        # Combine features
        # alpha_power shape: (n_epochs, n_alpha_electrodes)
        # beta_power shape: (n_epochs, n_beta_electrodes)
        feature_matrix = np.hstack([alpha_power, beta_power])
        
        # Create feature names
        alpha_features = [f"alpha_{ch}" for ch in electrodes_alpha]
        beta_features = [f"beta_{ch}" for ch in electrodes_beta]
        feature_names = alpha_features + beta_features
        
        # Save to CSV
        output_path.parent.mkdir(parents=True, exist_ok=True)
        import pandas as pd
        df = pd.DataFrame(feature_matrix, columns=feature_names)
        
        # Add epoch labels if available
        if hasattr(epochs, 'events') and epochs.events is not None:
            # Extract condition labels from events
            # Assuming events are structured as [time, 0, condition_code]
            conditions = epochs.events[:, 2]
            df['condition'] = conditions
        
        df.to_csv(output_path, index=False)
        logger.info(f"Saved feature matrix to {output_path}")
        
        result = {
            "status": "success",
            "n_epochs": len(epochs),
            "n_features": feature_matrix.shape[1],
            "alpha_electrodes": electrodes_alpha,
            "beta_electrodes": electrodes_beta,
            "alpha_band": freq_band_alpha,
            "beta_band": freq_band_beta,
            "feature_names": feature_names,
            "output_path": str(output_path)
        }
        
        log_stage_end(logger, "Feature Extraction", result)
        return result
        
    except Exception as e:
        logger.error(f"Feature extraction failed: {e}")
        log_stage_end(logger, "Feature Extraction", {"status": "failed", "error": str(e)})
        raise

def main():
    """Main entry point for feature extraction."""
    paths = get_paths()
    epochs_path = paths["data_processed"] / "epochs_cleaned.fif"
    output_path = paths["data_processed"] / "features_matrix.csv"
    
    # Define electrodes and frequency bands
    # Alpha: P, Pz, P4
    electrodes_alpha = ["P", "Pz", "P4"]
    # Beta: F3, Fz, F4
    electrodes_beta = ["F3", "Fz", "F4"]
    
    freq_band_alpha = ALPHA_BAND
    freq_band_beta = BETA_BAND
    
    # Run extraction
    result = run_extraction(
        epochs_path=epochs_path,
        output_path=output_path,
        electrodes_alpha=electrodes_alpha,
        electrodes_beta=electrodes_beta,
        freq_band_alpha=freq_band_alpha,
        freq_band_beta=freq_band_beta,
        baseline=(-0.2, 0.0)
    )
    
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()