import os
import sys
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple
import numpy as np
import mne
from scipy.signal import welch
from scipy.stats import pearsonr

# Import from local utils to ensure project structure compliance
try:
    from utils.config import BANDS, LOWER_FREQ_HZ
except ImportError:
    # Fallback if run directly without package structure, though project structure assumes utils is present
    BANDS = ['delta', 'theta', 'alpha', 'beta', 'gamma']
    LOWER_FREQ_HZ = 1.0

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ROI Pairs as defined in T024
ROI_PAIRS = [
    ('C3', 'C4'),
    ('C3', 'Cz'),
    ('C4', 'Cz')
]

def compute_welch_power(epochs: mne.Epochs, sfreq: float) -> Dict[str, np.ndarray]:
    """
    Compute Welch's Power Spectral Density for each channel and band.
    Returns a dict: {channel: {band: mean_power}}
    """
    data = epochs.get_data()  # Shape: (n_epochs, n_channels, n_times)
    n_epochs, n_channels, n_times = data.shape
    channel_names = epochs.ch_names

    # Frequencies and PSDs
    # Using Welch's method: 2s windows, 50% overlap
    f, Pxx = welch(data, fs=sfreq, nperseg=int(2 * sfreq), noverlap=int(1 * sfreq), axis=-1)
    
    # Pxx shape: (n_epochs, n_channels, n_freqs)
    
    features = {}
    for i, ch_name in enumerate(channel_names):
        features[ch_name] = {}
        for band_name, (f_low, f_high) in BANDS.items():
            # Filter frequencies
            mask = (f >= f_low) & (f <= f_high)
            if np.any(mask):
                # Mean power across frequency band, then average across epochs
                band_power = np.mean(Pxx[:, i, mask], axis=1)
                features[ch_name][band_name] = float(np.mean(band_power))
            else:
                features[ch_name][band_name] = 0.0
    
    return features

def compute_plv(signal1: np.ndarray, signal2: np.ndarray, sfreq: float, 
                fmin: float, fmax: float) -> float:
    """
    Compute Phase Locking Value (PLV) between two signals in a specific frequency band.
    signal1, signal2: shape (n_epochs, n_times)
    """
    # Bandpass filter signals (simple FIR for this calculation, or use mne)
    # Since we are working with epochs data (n_epochs, n_times), we compute PLV across epochs
    # PLV = | mean(exp(j * (phi1 - phi2))) |
    
    # Using Hilbert transform to extract instantaneous phase
    # Filter first
    from scipy.signal import butter, filtfilt
    b, a = butter(4, [fmin / (sfreq / 2), fmax / (sfreq / 2)], btype='band')
    
    sig1_filt = filtfilt(b, a, signal1, axis=1)
    sig2_filt = filtfilt(b, a, signal2, axis=1)
    
    # Hilbert transform
    analytic1 = mne.filter.hilbert(sig1_filt, sfreq, N=None, copy=True, n_jobs=1)
    analytic2 = mne.filter.hilbert(sig2_filt, sfreq, N=None, copy=True, n_jobs=1)
    
    # Extract phases
    phase1 = np.angle(analytic1)
    phase2 = np.angle(analytic2)
    
    # Phase difference
    phase_diff = phase1 - phase2
    
    # PLV: magnitude of mean of complex exponentials
    plv = np.abs(np.mean(np.exp(1j * phase_diff), axis=1))
    
    return float(np.mean(plv))

def compute_wpli(signal1: np.ndarray, signal2: np.ndarray, sfreq: float,
                 fmin: float, fmax: float) -> float:
    """
    Compute Weighted Phase Lag Index (wPLI).
    wPLI reduces sensitivity to volume conduction by weighting by the imaginary part.
    """
    from scipy.signal import butter, filtfilt
    
    b, a = butter(4, [fmin / (sfreq / 2), fmax / (sfreq / 2)], btype='band')
    
    sig1_filt = filtfilt(b, a, signal1, axis=1)
    sig2_filt = filtfilt(b, a, signal2, axis=1)
    
    # Cross-spectrum (imaginary part)
    # Using Hilbert for cross-spectral density estimation in time domain
    analytic1 = mne.filter.hilbert(sig1_filt, sfreq, N=None, copy=True, n_jobs=1)
    analytic2 = mne.filter.hilbert(sig2_filt, sfreq, N=None, copy=True, n_jobs=1)
    
    # Cross spectrum: X1 * conj(X2)
    cross_spec = analytic1 * np.conj(analytic2)
    
    # Imaginary part
    imag_part = np.imag(cross_spec)
    
    # wPLI calculation
    # wPLI = |E[sign(Im(X1 X2*) * |Im(X1 X2*)|)]| / E[|Im(X1 X2*)|]
    # Simplified: Mean of (Im * |Im|) / Mean of |Im|
    
    numerator = np.mean(np.sign(imag_part) * np.abs(imag_part), axis=1)
    denominator = np.mean(np.abs(imag_part), axis=1)
    
    # Avoid division by zero
    wpli = np.divide(numerator, denominator, out=np.zeros_like(numerator), where=denominator!=0)
    
    return float(np.mean(np.abs(wpli)))

def extract_connectivity_features(epochs: mne.Epochs, sfreq: float) -> Dict[str, float]:
    """
    Extract PLV and wPLI for specified ROI pairs across all bands.
    """
    channel_names = epochs.ch_names
    data = epochs.get_data()  # (n_epochs, n_channels, n_times)
    ch_to_idx = {ch: i for i, ch in enumerate(channel_names)}
    
    features = {}
    
    # Define bands with frequencies
    band_freqs = {
        'delta': (1.0, 4.0),
        'theta': (4.0, 8.0),
        'alpha': (8.0, 13.0),
        'beta': (13.0, 30.0),
        'gamma': (30.0, 45.0)
    }
    
    for ch1, ch2 in ROI_PAIRS:
        if ch1 not in ch_to_idx or ch2 not in ch_to_idx:
            logger.warning(f"Channel pair {ch1}-{ch2} not found in data. Skipping.")
            continue
        
        idx1 = ch_to_idx[ch1]
        idx2 = ch_to_idx[ch2]
        
        sig1 = data[:, idx1, :]
        sig2 = data[:, idx2, :]
        
        for band_name, (fmin, fmax) in band_freqs.items():
            # PLV
            plv_val = compute_plv(sig1, sig2, sfreq, fmin, fmax)
            features[f'PLV_{ch1}_{ch2}_{band_name}'] = plv_val
            
            # wPLI
            wpli_val = compute_wpli(sig1, sig2, sfreq, fmin, fmax)
            features[f'wPLI_{ch1}_{ch2}_{band_name}'] = wpli_val
    
    return features

def extract_spectral_features(epochs: mne.Epochs) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Extract spectral power and connectivity features.
    Returns: (spectral_features, connectivity_features)
    """
    sfreq = epochs.info['sfreq']
    
    # Spectral Power
    spectral_data = compute_welch_power(epochs, sfreq)
    
    # Connectivity
    connectivity_data = extract_connectivity_features(epochs, sfreq)
    
    return spectral_data, connectivity_data

def process_epochs_file(input_path: str, output_csv: str) -> None:
    """
    Load epochs, extract features, and append to CSV.
    """
    logger.info(f"Loading epochs from {input_path}")
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Epochs file not found: {input_path}")
    
    epochs = mne.read_epochs(input_path, preload=True)
    
    logger.info("Extracting spectral and connectivity features...")
    spectral_features, connectivity_features = extract_spectral_features(epochs)
    
    # Combine features
    # We expect one subject per file in this pipeline stage, or we aggregate.
    # Assuming single subject per file for now based on T023 structure.
    # We need to extract subject ID from filename or metadata.
    
    subject_id = Path(input_path).stem.replace('epochs_', '')
    if subject_id == 'epochs':
        subject_id = 'unknown'
    
    # Flatten features
    all_features = {'subject_id': subject_id}
    all_features.update(spectral_features) # This will overwrite if keys clash, but keys are distinct
    
    # Actually, spectral_features is {channel: {band: val}}. We need to flatten it.
    flat_spectral = {}
    for ch, bands in spectral_features.items():
        for band, val in bands.items():
            flat_spectral[f'Power_{ch}_{band}'] = val
    
    all_features = {'subject_id': subject_id}
    all_features.update(flat_spectral)
    all_features.update(connectivity_features)
    
    # Append to CSV
    import csv
    file_exists = os.path.isfile(output_csv)
    
    with open(output_csv, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=all_features.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(all_features)
    
    logger.info(f"Features appended to {output_csv}")

def main():
    """
    Main entry point for feature extraction.
    Expects data/processed/epochs.fif to exist (from T018).
    Outputs to data/processed/spectral_power.csv (appending connectivity).
    """
    base_path = Path(__file__).parent.parent
    epochs_path = base_path / 'data' / 'processed' / 'epochs.fif'
    output_csv = base_path / 'data' / 'processed' / 'spectral_power.csv'
    
    if not epochs_path.exists():
        logger.error(f"Epochs file not found at {epochs_path}. Run T018 first.")
        sys.exit(1)
    
    # Check if CSV exists (from T023)
    if not output_csv.exists():
        # If T023 hasn't run or failed to create the file, we might need to handle that.
        # However, T024 says "Append results to spectral_power.csv".
        # If the file doesn't exist, we create it with headers.
        logger.warning(f"Output CSV {output_csv} not found. Creating new file.")
    
    try:
        process_epochs_file(str(epochs_path), str(output_csv))
        logger.info("T024 Connectivity extraction completed successfully.")
    except Exception as e:
        logger.error(f"Error during connectivity extraction: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
