import numpy as np
import mne
from typing import Dict, List, Optional, Tuple
import pandas as pd

EPSILON = 1e-9

def compute_psd_welch(
    epochs: mne.Epochs,
    fmin: float,
    fmax: float,
    n_fft: Optional[int] = None,
    n_overlap: Optional[int] = None,
    n_cycles: float = 2.0,
    average: bool = True
) -> np.ndarray:
    """
    Compute Power Spectral Density (PSD) using Welch's method.
    
    Args:
        epochs: MNE Epochs object.
        fmin: Minimum frequency to consider.
        fmax: Maximum frequency to consider.
        n_fft: FFT window size.
        n_overlap: Number of points to overlap between segments.
        n_cycles: Number of cycles for multitaper.
        average: If True, average across epochs.
        
    Returns:
        Array of PSD values (shape: [n_epochs, n_channels, n_freqs] or [n_channels, n_freqs]).
    """
    # Use MNE's built-in psd_welch
    psd, freqs = mne.time_frequency.psd_welch(
        epochs,
        fmin=fmin,
        fmax=fmax,
        n_fft=n_fft,
        n_overlap=n_overlap,
        n_cycles=n_cycles,
        average=False
    )
    
    if average:
        psd = np.mean(psd, axis=0)
    
    return psd, freqs

def extract_band_power(
    psd: np.ndarray,
    freqs: np.ndarray,
    band: Tuple[float, float]
) -> np.ndarray:
    """
    Extract mean power within a specific frequency band.
    
    Args:
        psd: Power spectral density values.
        freqs: Frequency values corresponding to psd.
        band: Tuple of (fmin, fmax) for the band.
        
    Returns:
        Mean power in the specified band.
    """
    fmin, fmax = band
    band_mask = (freqs >= fmin) & (freqs <= fmax)
    if not np.any(band_mask):
        return np.zeros(psd.shape[:-1])
    
    return np.mean(psd[..., band_mask], axis=-1)

def compute_theta_alpha_ratio(
    theta_power: np.ndarray,
    alpha_power: np.ndarray
) -> np.ndarray:
    """
    Compute the theta/alpha power ratio.
    
    Handles division by zero by adding a small epsilon to the denominator.
    
    Args:
        theta_power: Theta band power values.
        alpha_power: Alpha band power values.
        
    Returns:
        Theta/Alpha ratio.
    """
    return theta_power / (alpha_power + EPSILON)

def extract_features(
    epochs: mne.Epochs,
    theta_band: Tuple[float, float] = (4.0, 7.0),
    alpha_band: Tuple[float, float] = (8.0, 12.0),
    fmin: float = 1.0,
    fmax: float = 45.0
) -> pd.DataFrame:
    """
    Extract spectral power features from epochs.
    
    Args:
        epochs: MNE Epochs object.
        theta_band: Theta frequency band.
        alpha_band: Alpha frequency band.
        fmin: Minimum frequency for PSD calculation.
        fmax: Maximum frequency for PSD calculation.
        
    Returns:
        DataFrame with features per epoch and channel.
    """
    # Compute PSD
    psd, freqs = compute_psd_welch(epochs, fmin=fmin, fmax=fmax, average=False)
    
    # Extract band powers
    theta_power = extract_band_power(psd, freqs, theta_band)
    alpha_power = extract_band_power(psd, freqs, alpha_band)
    
    # Compute ratio
    tar = compute_theta_alpha_ratio(theta_power, alpha_power)
    
    # Create DataFrame
    n_epochs, n_channels = theta_power.shape
    feature_data = []
    
    for i in range(n_epochs):
        for j, ch_name in enumerate(epochs.ch_names):
            feature_data.append({
                'epoch_idx': i,
                'channel': ch_name,
                'theta_power': float(theta_power[i, j]),
                'alpha_power': float(alpha_power[i, j]),
                'theta_alpha_ratio': float(tar[i, j])
            })
    
    return pd.DataFrame(feature_data)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        # This is a placeholder for testing
        print("Feature extraction module loaded successfully.")
        print(f"EPSILON constant: {EPSILON}")
    else:
        print("Usage: python extract.py [data_dir]")
