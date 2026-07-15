"""
Preprocessing pipeline for EEG data using MNE-Python.

Implements:
- Bandpass filtering (1-40 Hz)
- ICA artifact removal
- Epoching (10s as per config)
- Artifact rejection (>50% rejection threshold)
- SNR flagging (<10dB)
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import mne
import numpy as np
from scipy import signal
import hashlib

# Import configuration
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import (
    EPOCH_LENGTH_SEC, 
    BANDPASS_FREQS, 
    ARTIFACT_REJECTION_THRESHOLD, 
    SNR_THRESHOLD_DB,
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
    QUALITY_DIR
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_raw_eeg(file_path: Path) -> mne.io.Raw:
    """
    Load raw EEG data from file (EDF, BDF, etc.).
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Raw EEG file not found: {file_path}")
    
    logger.info(f"Loading raw EEG from {file_path}")
    raw = mne.io.read_raw_edf(str(file_path), preload=True, verbose=False)
    return raw

def bandpass_filter(raw: mne.io.Raw, l_freq: float = 1.0, h_freq: float = 40.0) -> mne.io.Raw:
    """
    Apply bandpass filter to raw data.
    """
    logger.info(f"Applying bandpass filter: {l_freq}-{h_freq} Hz")
    raw_filtered = raw.copy()
    raw_filtered.filter(l_freq=l_freq, h_freq=h_freq, method='fir', verbose=False)
    return raw_filtered

def compute_snr(raw: mne.io.Raw) -> float:
    """
    Compute Signal-to-Noise Ratio (SNR) in dB.
    SNR = 10 * log10(signal_power / noise_power)
    Signal power: power in the passband (1-40 Hz)
    Noise power: estimated from high-frequency noise (e.g., >40 Hz, but since we filtered, 
                 we estimate noise from the residual variance or a known noise floor).
    Here, we approximate noise as the standard deviation of the signal after high-pass filtering 
    at a higher frequency (e.g., 45Hz) if possible, or use a heuristic based on the signal's 
    variance in the stopband of a hypothetical filter. 
    For simplicity in this pipeline: 
    SNR is estimated as 10 * log10(var(signal) / var(noise_estimate)).
    We estimate noise as the standard deviation of the difference between the raw signal 
    and a low-pass filtered version (e.g., 100Hz) or simply use the variance of the signal 
    in a high-frequency band if available. 
    Given we only have 1-40Hz data, we estimate noise as the variance of the signal 
    above a certain threshold (e.g., using the median absolute deviation scaled).
    
    Alternative robust SNR: 
    SNR (dB) = 10 * log10( mean(signal^2) / mean(noise^2) )
    We approximate noise by taking the median absolute deviation (MAD) of the signal 
    and scaling it to standard deviation (MAD * 1.4826 for Gaussian).
    """
    data = raw.get_data()
    # Flatten data across channels and time for a global estimate
    flat_data = data.flatten()
    
    # Estimate noise using Median Absolute Deviation (MAD)
    mad = np.median(np.abs(flat_data - np.median(flat_data)))
    noise_std = mad * 1.4826
    if noise_std == 0:
        noise_std = 1e-9
    
    signal_power = np.var(flat_data)
    noise_power = noise_std ** 2
    
    snr_db = 10 * np.log10(signal_power / noise_power)
    return snr_db

def run_ica(raw: mne.io.Raw, n_components: int = 20) -> mne.preprocessing.ICA:
    """
    Run Independent Component Analysis (ICA) for artifact removal.
    """
    logger.info(f"Running ICA with {n_components} components")
    ica = mne.preprocessing.ICA(n_components=n_components, method='fastica', random_state=42, verbose=False)
    ica.fit(raw)
    return ica

def apply_ica(ica: mne.preprocessing.ICA, raw: mne.io.Raw, 
              exclude_components: List[int]) -> mne.io.Raw:
    """
    Apply ICA to remove artifact components.
    """
    logger.info(f"Applying ICA, excluding components: {exclude_components}")
    raw_ica = raw.copy()
    ica.apply(raw_ica, exclude=exclude_components)
    return raw_ica

def create_epochs(raw: mne.io.Raw, event_id: Optional[int] = None, 
                  tmin: float = 0.0, tmax: float = 10.0) -> mne.Epochs:
    """
    Create epochs of fixed duration (10s as per config).
    For resting-state data without events, we create epochs based on time segments.
    """
    logger.info(f"Creating epochs: {tmax - tmin} seconds")
    
    # If no events, create artificial events at regular intervals
    sfreq = raw.info['sfreq']
    duration = tmax - tmin
    n_samples = int(duration * sfreq)
    
    # Generate events at regular intervals
    n_events = int(raw.times[-1] / duration)
    events = np.zeros((n_events, 3), dtype=int)
    for i in range(n_events):
        events[i, 0] = int(i * duration * sfreq)  # sample index
        events[i, 1] = 0  # dummy
        events[i, 2] = 1  # event ID
    
    epochs = mne.Epochs(raw, events, event_id=1, tmin=tmin, tmax=tmax, 
                        baseline=None, verbose=False)
    return epochs

def detect_artifacts(epochs: mne.Epochs, threshold: float = 150e-6) -> np.ndarray:
    """
    Detect epochs with artifacts based on amplitude threshold.
    Returns a boolean array where True indicates an artifact epoch.
    """
    data = epochs.get_data()  # shape: (n_epochs, n_channels, n_times)
    # Check for amplitude exceeding threshold in any channel
    artifact_mask = np.any(np.abs(data) > threshold, axis=(1, 2))
    return artifact_mask

def preprocess_file(file_path: Path) -> Dict[str, Any]:
    """
    Full preprocessing pipeline for a single EEG file.
    Returns a dictionary with processed data, flags, and metadata.
    """
    result = {
        'file_path': str(file_path),
        'status': 'success',
        'snr_db': None,
        'n_epochs_total': 0,
        'n_epochs_rejected': 0,
        'rejected_ratio': 0.0,
        'snr_flag': None,
        'artifact_rejection_flag': None,
        'processed_epochs_path': None
    }
    
    try:
        # 1. Load raw data
        raw = load_raw_eeg(file_path)
        
        # 2. Bandpass filter
        raw = bandpass_filter(raw, l_freq=BANDPASS_FREQS[0], h_freq=BANDPASS_FREQS[1])
        
        # 3. Compute SNR
        snr = compute_snr(raw)
        result['snr_db'] = snr
        if snr < SNR_THRESHOLD_DB:
            result['snr_flag'] = 'Low Signal Quality'
            logger.warning(f"Low SNR detected: {snr:.2f} dB < {SNR_THRESHOLD_DB} dB")
        else:
            result['snr_flag'] = 'Good Signal Quality'
        
        # 4. Run ICA
        ica = run_ica(raw)
        
        # 5. Detect and exclude artifact components (simple heuristic: high variance)
        # For a more robust approach, we would use automated detection (e.g., ADJUST, MARA)
        # Here, we exclude components with high variance as a placeholder
        variances = np.var(ica.get_sources(raw).get_data(), axis=1)
        exclude_components = np.where(variances > np.mean(variances) * 2)[0].tolist()
        
        # 6. Apply ICA
        raw = apply_ica(ica, raw, exclude_components)
        
        # 7. Create epochs
        epochs = create_epochs(raw, tmin=0.0, tmax=EPOCH_LENGTH_SEC)
        result['n_epochs_total'] = len(epochs)
        
        # 8. Detect artifacts in epochs
        artifact_mask = detect_artifacts(epochs)
        n_rejected = np.sum(artifact_mask)
        result['n_epochs_rejected'] = int(n_rejected)
        result['rejected_ratio'] = n_rejected / len(epochs) if len(epochs) > 0 else 0.0
        
        # 9. Reject epochs with >50% artifacts
        if result['rejected_ratio'] > ARTIFACT_REJECTION_THRESHOLD:
            result['artifact_rejection_flag'] = 'Rejected'
            logger.warning(f"High artifact ratio: {result['rejected_ratio']:.2f} > {ARTIFACT_REJECTION_THRESHOLD}")
            # Reject all epochs for this file
            epochs_clean = mne.EpochsArray(np.empty((0, len(epochs.ch_names), int(EPOCH_LENGTH_SEC * epochs.info['sfreq']))), 
                                            info=epochs.info)
        else:
            result['artifact_rejection_flag'] = 'Accepted'
            # Keep non-artifact epochs
            epochs_clean = epochs[~artifact_mask]
        
        # 10. Save processed epochs
        processed_dir = PROCESSED_DATA_DIR / file_path.stem
        processed_dir.mkdir(parents=True, exist_ok=True)
        output_path = processed_dir / f"epochs-{file_path.stem}.fif"
        epochs_clean.save(output_path, overwrite=True)
        result['processed_epochs_path'] = str(output_path)
        
        # 11. Save metadata
        metadata_path = processed_dir / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(result, f, indent=2)
        
    except Exception as e:
        logger.error(f"Error processing {file_path}: {e}")
        result['status'] = 'failed'
        result['error'] = str(e)
    
    return result

def main():
    """
    Main entry point for preprocessing pipeline.
    Processes all files in RAW_DATA_DIR and generates outputs in PROCESSED_DATA_DIR.
    """
    logger.info("Starting preprocessing pipeline")
    
    # Ensure directories exist
    from config import ensure_dirs
    ensure_dirs()
    
    # Find all EEG files
    eeg_files = list(RAW_DATA_DIR.glob("*.edf")) + list(RAW_DATA_DIR.glob("*.bdf")) + list(RAW_DATA_DIR.glob("*.vhdr"))
    
    if not eeg_files:
        logger.warning("No EEG files found in RAW_DATA_DIR. Skipping preprocessing.")
        return
    
    logger.info(f"Found {len(eeg_files)} EEG files to process")
    
    results = []
    for file_path in eeg_files:
        logger.info(f"Processing: {file_path}")
        result = preprocess_file(file_path)
        results.append(result)
    
    # Save summary report
    summary_path = QUALITY_DIR / "preprocessing_report.json"
    with open(summary_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Preprocessing complete. Summary saved to {summary_path}")

if __name__ == "__main__":
    main()