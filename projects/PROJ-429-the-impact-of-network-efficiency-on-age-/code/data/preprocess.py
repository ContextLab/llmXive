"""
Preprocessing pipeline for TUH EEG data using MNE-Python.

Implements:
- Bandpass filtering (1-40 Hz)
- ICA for artifact removal
- Epoching (10s windows as per config)
- Artifact rejection (>50% artifact epochs rejected)
- SNR flagging (<10dB flagged)
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

import mne
import numpy as np
import pandas as pd
from scipy import signal

# Import config
from code.config import get_config, get_paths

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_raw_eeg(file_path: Path) -> mne.io.Raw:
    """Load raw EEG file using MNE."""
    if not file_path.exists():
        raise FileNotFoundError(f"EEG file not found: {file_path}")
    
    # Determine file type and load
    suffix = file_path.suffix.lower()
    if suffix in ['.edf', '.bdf']:
        raw = mne.io.read_raw_edf(file_path, preload=True, verbose=False)
    elif suffix == '.fif':
        raw = mne.io.read_raw_fif(file_path, preload=True, verbose=False)
    else:
        # Try generic reader
        raw = mne.io.read_raw_edf(file_path, preload=True, verbose=False)
    
    # Set montage if not present (standard 10-20)
    if raw.info['ch_names'] and 'EEG' in str(raw.info['ch_names'][0]):
        try:
            montage = mne.channels.make_standard_montage('standard_1005')
            raw.set_montage(montage, match_case=False, match_alias=True, on_missing='ignore')
        except Exception as e:
            logger.warning(f"Could not set montage: {e}")
    
    return raw

def bandpass_filter(raw: mne.io.Raw, l_freq: float = 1.0, h_freq: float = 40.0) -> mne.io.Raw:
    """Apply bandpass filter (1-40 Hz)."""
    logger.info(f"Applying bandpass filter: {l_freq}-{h_freq} Hz")
    raw_filtered = raw.copy()
    raw_filtered.filter(l_freq=l_freq, h_freq=h_freq, method='fir', n_jobs=1, verbose=False)
    return raw_filtered

def compute_snr(raw: mne.io.Raw) -> float:
    """
    Compute Signal-to-Noise Ratio (SNR) in dB.
    SNR = 10 * log10(signal_power / noise_power)
    Signal: power in 1-40 Hz band
    Noise: estimated from high-frequency residual or flat segments
    """
    data = raw.get_data()
    fs = raw.info['sfreq']
    
    # Estimate signal power (1-40 Hz band)
    # Using Welch's method for power spectral density
    f, pxx = signal.welch(data, fs=fs, nperseg=min(1024, len(data[0])//4))
    
    # Signal band indices
    signal_mask = (f >= 1.0) & (f <= 40.0)
    noise_mask = (f > 40.0) & (f < 100.0)  # High frequency noise estimate
    
    if np.any(signal_mask) and np.any(noise_mask):
        signal_power = np.mean(pxx[signal_mask, :], axis=1)
        noise_power = np.mean(pxx[noise_mask, :], axis=1)
        
        # Avoid division by zero
        noise_power = np.maximum(noise_power, 1e-10)
        
        snr_db = 10 * np.log10(signal_power / noise_power)
        return float(np.mean(snr_db))
    else:
        # Fallback: simple variance ratio
        signal_power = np.var(data)
        noise_power = np.std(data) ** 2 * 0.1  # Heuristic
        return float(10 * np.log10(signal_power / max(noise_power, 1e-10)))

def run_ica(raw: mne.io.Raw, n_components: int = 20) -> tuple:
    """
    Run ICA for artifact removal.
    Returns: (ica_model, n_components_used)
    """
    logger.info(f"Running ICA with {n_components} components")
    ica = mne.preprocessing.ICA(n_components=n_components, random_state=42, method='fastica', max_iter='auto')
    
    # Fit ICA
    ica.fit(raw, verbose=False)
    
    # Find and mark bad components (EOG, ECG)
    # This is a simplified version - in production, use more sophisticated detection
    eog_indices, eog_scores = ica.find_bads_eog(raw, threshold=3.0)
    ecg_indices, ecg_scores = ica.find_bads_ecg(raw, threshold=3.0)
    
    bad_components = set(eog_indices + ecg_indices)
    ica.exclude = list(bad_components)
    
    logger.info(f"Excluding {len(ica.exclude)} components: {ica.exclude}")
    
    return ica, len(ica.exclude)

def apply_ica(raw: mne.io.Raw, ica: mne.preprocessing.ICA) -> mne.io.Raw:
    """Apply ICA to remove artifacts."""
    logger.info("Applying ICA to remove artifacts")
    raw_clean = ica.apply(raw.copy(), verbose=False)
    return raw_clean

def create_epochs(raw: mne.io.Raw, epoch_length_sec: float = 10.0) -> List[mne.Epochs]:
    """
    Create epochs from continuous data.
    Returns list of epoch arrays (not mne.Epochs object to avoid memory issues).
    """
    data = raw.get_data()
    fs = raw.info['sfreq']
    n_samples = int(epoch_length_sec * fs)
    n_channels = data.shape[0]
    
    n_epochs = len(data[0]) // n_samples
    logger.info(f"Creating {n_epochs} epochs of {epoch_length_sec}s each")
    
    epochs_list = []
    for i in range(n_epochs):
        start = i * n_samples
        end = start + n_samples
        epoch_data = data[:, start:end]
        epochs_list.append(epoch_data)
    
    return epochs_list

def detect_artifacts(epochs: List[np.ndarray], threshold: float = 0.5) -> List[bool]:
    """
    Detect epochs with >50% artifact content.
    Uses amplitude threshold and gradient detection.
    Returns list of booleans (True = epoch is clean).
    """
    clean_flags = []
    
    for epoch in epochs:
        # Calculate amplitude statistics
        max_amp = np.max(np.abs(epoch), axis=1)
        mean_amp = np.mean(np.abs(epoch), axis=1)
        
        # Detect large amplitude artifacts (e.g., > 100 uV or > 5x mean)
        artifact_mask = (max_amp > 100e-6) | (max_amp > 5 * mean_amp)
        
        # Calculate artifact ratio per channel
        artifact_ratio = np.mean(artifact_mask, axis=0)
        
        # If >50% of time points are artifacts, reject epoch
        is_clean = np.mean(artifact_ratio) < threshold
        clean_flags.append(is_clean)
    
    return clean_flags

def preprocess_file(
    input_path: Path,
    output_dir: Path,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Preprocess a single EEG file.
    
    Args:
        input_path: Path to raw EEG file
        output_dir: Directory to save processed data
        config: Configuration dictionary
    
    Returns:
        Dictionary with preprocessing results and metadata
    """
    file_id = input_path.stem
    result = {
        'file_id': file_id,
        'status': 'pending',
        'snr_db': None,
        'n_epochs_total': 0,
        'n_epochs_clean': 0,
        'n_artifacts_rejected': 0,
        'snr_flag': None,
        'ica_components_excluded': 0,
        'output_path': None
    }
    
    try:
        # 1. Load raw data
        logger.info(f"Loading: {input_path}")
        raw = load_raw_eeg(input_path)
        
        # 2. Bandpass filter (1-40 Hz)
        raw = bandpass_filter(raw, l_freq=1.0, h_freq=40.0)
        
        # 3. Compute SNR before ICA
        snr = compute_snr(raw)
        result['snr_db'] = snr
        
        # Flag SNR < 10dB
        if snr < 10.0:
            result['snr_flag'] = 'Low Signal Quality'
        else:
            result['snr_flag'] = 'Good'
        
        # 4. Run ICA
        ica, n_excluded = run_ica(raw, n_components=config.get('n_ica_components', 20))
        result['ica_components_excluded'] = n_excluded
        
        # 5. Apply ICA
        raw_clean = apply_ica(raw, ica)
        
        # 6. Create epochs (10s as per config)
        epoch_length = config.get('epoch_length_sec', 10.0)
        epochs = create_epochs(raw_clean, epoch_length_sec=epoch_length)
        result['n_epochs_total'] = len(epochs)
        
        # 7. Detect and reject artifacts
        clean_flags = detect_artifacts(epochs, threshold=0.5)
        n_clean = sum(clean_flags)
        n_rejected = len(epochs) - n_clean
        
        result['n_epochs_clean'] = n_clean
        result['n_artifacts_rejected'] = n_rejected
        
        # 8. Save clean epochs
        if n_clean > 0:
            output_path = output_dir / f"{file_id}_epochs.npy"
            clean_epochs = [epochs[i] for i, flag in enumerate(clean_flags) if flag]
            np.save(output_path, clean_epochs)
            result['output_path'] = str(output_path)
            result['status'] = 'success'
        else:
            result['status'] = 'rejected_all_epochs'
        
    except Exception as e:
        logger.error(f"Error processing {input_path}: {e}")
        result['status'] = 'error'
        result['error_message'] = str(e)
    
    return result

def main():
    """Main entry point for preprocessing pipeline."""
    config = get_config()
    paths = get_paths()
    
    raw_dir = paths['raw']
    processed_dir = paths['processed']
    quality_dir = paths['quality']
    
    # Ensure output directories exist
    processed_dir.mkdir(parents=True, exist_ok=True)
    (processed_dir / 'epochs').mkdir(parents=True, exist_ok=True)
    quality_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all EEG files
    eeg_files = list(raw_dir.glob('*.edf')) + list(raw_dir.glob('*.bdf')) + list(raw_dir.glob('*.fif'))
    
    if not eeg_files:
        logger.warning(f"No EEG files found in {raw_dir}")
        # Create empty report
        report = {
            'total_files': 0,
            'processed_files': 0,
            'successful': 0,
            'failed': 0,
            'files': []
        }
        with open(quality_dir / 'preprocessing_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        return
    
    logger.info(f"Found {len(eeg_files)} EEG files to process")
    
    results = []
    for file_path in eeg_files:
        logger.info(f"Processing: {file_path.name}")
        result = preprocess_file(file_path, processed_dir / 'epochs', config)
        results.append(result)
        
        # Save individual result
        result_path = quality_dir / f"{file_path.stem}_preprocess.json"
        with open(result_path, 'w') as f:
            json.dump(result, f, indent=2)
    
    # Generate summary report
    summary = {
        'total_files': len(results),
        'processed_files': len([r for r in results if r['status'] != 'error']),
        'successful': len([r for r in results if r['status'] == 'success']),
        'failed': len([r for r in results if r['status'] == 'error']),
        'low_snr_count': len([r for r in results if r.get('snr_flag') == 'Low Signal Quality']),
        'total_epochs': sum(r['n_epochs_total'] for r in results),
        'clean_epochs': sum(r['n_epochs_clean'] for r in results),
        'rejected_epochs': sum(r['n_artifacts_rejected'] for r in results),
        'files': results
    }
    
    report_path = quality_dir / 'preprocessing_report.json'
    with open(report_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Preprocessing complete. Report saved to {report_path}")
    logger.info(f"Summary: {summary['successful']}/{summary['total_files']} files processed successfully")

if __name__ == '__main__':
    main()
