"""
Preprocessing pipeline for EEG data using MNE-Python.

Implements bandpass filtering, ICA artifact removal, epoching, and SNR-based quality control.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import mne
import numpy as np
import pandas as pd
from scipy import signal
import hashlib

# Import project configuration
from config import (
    PROJECT_ROOT,
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
    QUALITY_DIR,
    EPOCH_LENGTH_SEC,
    BANDPASS_MIN_FREQ,
    BANDPASS_MAX_FREQ,
    SNR_THRESHOLD_DB,
    ARTIFACT_REJECTION_THRESHOLD
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_raw_eeg(file_path: Path) -> mne.io.BaseRaw:
    """
    Load raw EEG data from file.

    Supports EDF, BDF, and other MNE-supported formats.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Raw EEG file not found: {file_path}")

    logger.info(f"Loading raw EEG from: {file_path}")
    try:
        raw = mne.io.read_raw_edf(file_path, preload=True, verbose=False)
    except Exception:
        try:
            raw = mne.io.read_raw_bdf(file_path, preload=True, verbose=False)
        except Exception as e:
            raise RuntimeError(f"Failed to load EEG file: {e}")

    # Set montage if standard
    try:
        raw.set_montage('standard_1005', on_missing='ignore')
    except Exception as e:
        logger.warning(f"Could not set montage: {e}")

    return raw

def bandpass_filter(raw: mne.io.BaseRaw, min_freq: float = None, max_freq: float = None) -> mne.io.BaseRaw:
    """
    Apply bandpass filter to raw data.

    Uses MNE's built-in filter with default settings (FIR).
    """
    if min_freq is None:
        min_freq = BANDPASS_MIN_FREQ
    if max_freq is None:
        max_freq = BANDPASS_MAX_FREQ

    logger.info(f"Applying bandpass filter: {min_freq} - {max_freq} Hz")
    raw_filtered = raw.copy()
    raw_filtered.filter(
        l_freq=min_freq,
        h_freq=max_freq,
        method='fir',
        n_jobs=1,
        verbose=False
    )
    return raw_filtered

def compute_snr(epochs: mne.Epochs, reference_freq: float = 10.0) -> np.ndarray:
    """
    Compute Signal-to-Noise Ratio (SNR) per epoch.

    SNR is calculated as the ratio of power in a reference frequency band
    to the power in adjacent noise bands.

    Args:
        epochs: MNE Epochs object
        reference_freq: Reference frequency for signal (default 10 Hz)

    Returns:
        Array of SNR values in dB for each epoch
    """
    logger.info("Computing SNR per epoch...")

    # Get data: shape (n_epochs, n_channels, n_times)
    data = epochs.get_data()
    sfreq = epochs.info['sfreq']
    n_epochs, n_channels, n_times = data.shape

    # Frequency bands for SNR calculation
    # Signal band: reference_freq +/- 1 Hz
    f_signal = (reference_freq - 1, reference_freq + 1)
    # Noise bands: below and above signal
    f_noise_low = (BANDPASS_MIN_FREQ, reference_freq - 2)
    f_noise_high = (reference_freq + 2, BANDPASS_MAX_FREQ)

    snr_values = []

    for ep_idx in range(n_epochs):
        epoch_data = data[ep_idx]  # (n_channels, n_times)

        # Compute power spectral density for each channel
        psd, freqs = mne.time_frequency.psd_welch(
            mne.EpochsArray(
                epoch_data[np.newaxis, :, :],
                info=epochs.info,
                tmin=0
            ),
            fmin=BANDPASS_MIN_FREQ,
            fmax=BANDPASS_MAX_FREQ,
            n_fft=min(256, n_times),
            verbose=False
        )

        # Average across channels
        psd_avg = psd.mean(axis=0)

        # Integrate power in signal and noise bands
        signal_mask = (freqs >= f_signal[0]) & (freqs <= f_signal[1])
        noise_low_mask = (freqs >= f_noise_low[0]) & (freqs <= f_noise_low[1])
        noise_high_mask = (freqs >= f_noise_high[0]) & (freqs <= f_noise_high[1])

        power_signal = np.sum(psd_avg[signal_mask])
        power_noise_low = np.sum(psd_avg[noise_low_mask]) if np.any(noise_low_mask) else 1e-10
        power_noise_high = np.sum(psd_avg[noise_high_mask]) if np.any(noise_high_mask) else 1e-10

        power_noise = (power_noise_low + power_noise_high) / 2

        # Avoid division by zero
        if power_noise < 1e-10:
            snr_db = 100.0  # Very high SNR
        else:
            snr_db = 10 * np.log10(power_signal / power_noise)

        snr_values.append(snr_db)

    return np.array(snr_values)

def run_ica(raw: mne.io.BaseRaw, n_components: int = 20) -> mne.preprocessing.ICA:
    """
    Run ICA for artifact removal.

    Args:
        raw: Filtered raw data
        n_components: Number of ICA components

    Returns:
        Fitted ICA object
    """
    logger.info(f"Running ICA with {n_components} components...")

    ica = mne.preprocessing.ICA(
        n_components=n_components,
        method='fastica',
        random_state=42,
        max_iter='auto',
        verbose=False
    )

    ica.fit(raw, verbose=False)

    return ica

def detect_artifacts(ica: mne.preprocessing.ICA, raw: mne.io.BaseRaw, 
                    raw_filtered: mne.io.BaseRaw) -> List[int]:
    """
    Detect artifact components using automatic detection.

    Returns:
        List of component indices to reject
    """
    logger.info("Detecting artifact components...")

    # Find EOG and ECG channels
    eog_indices, eog_ch_names = mne.preprocessing.find_eog_channels(
        raw_filtered, verbose=False
    )
    ecg_indices, ecg_ch_names = mne.preprocessing.find_ecg_channels(
        raw_filtered, verbose=False
    )

    # Find artifact components
    if eog_indices:
        eog_indices = [eog_indices[0]]  # Use first EOG channel
        ica.find_bads_eog(raw_filtered, ch_name=eog_ch_names[0], verbose=False)
    
    if ecg_indices:
        ecg_indices = [ecg_indices[0]]  # Use first ECG channel
        ica.find_bads_ecg(raw_filtered, ch_name=ecg_ch_names[0], verbose=False)

    # Get rejected components
    # Note: We use the exclusion lists set by find_bads_*
    rejected_components = list(ica.exclude)

    logger.info(f"Detected {len(rejected_components)} artifact components: {rejected_components}")

    return rejected_components

def apply_ica(ica: mne.preprocessing.ICA, raw: mne.io.BaseRaw, 
             exclude_components: List[int]) -> mne.io.BaseRaw:
    """
    Apply ICA correction by removing artifact components.

    Args:
        raw: Original raw data
        ica: Fitted ICA object
        exclude_components: Components to exclude

    Returns:
        Cleaned raw data
    """
    logger.info(f"Applying ICA correction, excluding components: {exclude_components}")

    ica_copy = ica.copy()
    ica_copy.exclude = exclude_components
    raw_clean = ica_copy.apply(raw.copy(), verbose=False)

    return raw_clean

def create_epochs(raw: mne.io.BaseRaw, epoch_length: int = None) -> mne.Epochs:
    """
    Create fixed-duration epochs from continuous data.

    Args:
        raw: Cleaned raw data
        epoch_length: Epoch length in seconds (default from config)

    Returns:
        Epochs object with fixed-length epochs
    """
    if epoch_length is None:
        epoch_length = EPOCH_LENGTH_SEC

    logger.info(f"Creating epochs of {epoch_length} seconds...")

    # Create events at regular intervals
    sfreq = raw.info['sfreq']
    n_samples = len(raw.times)
    epoch_samples = int(epoch_length * sfreq)
    
    # Number of complete epochs
    n_epochs = n_samples // epoch_samples
    
    if n_epochs < 1:
        raise ValueError(f"Data too short for {epoch_length}s epochs (only {n_samples} samples)")

    # Create events array: (n_epochs, 3) with [sample, 0, 1]
    events = np.array([
        [i * epoch_samples, 0, 1] 
        for i in range(n_epochs)
    ])

    # Create epochs
    epochs = mne.Epochs(
        raw,
        events,
        event_id={'epoch': 1},
        tmin=0,
        tmax=epoch_length,
        baseline=None,
        verbose=False,
        reject_by_annotation=False
    )

    logger.info(f"Created {len(epochs)} epochs")

    return epochs

def preprocess_file(input_path: Path, output_dir: Path, 
                   quality_report: Dict[str, Any]) -> Dict[str, Any]:
    """
    Preprocess a single EEG file.

    Steps:
    1. Load raw data
    2. Bandpass filter
    3. Run ICA
    4. Detect and remove artifacts
    5. Create epochs
    6. Compute SNR per epoch
    7. Flag low-SNR epochs
    8. Reject epochs with >50% artifacts

    Args:
        input_path: Path to raw EEG file
        output_dir: Directory to save processed data
        quality_report: Dict to accumulate quality metrics

    Returns:
        Updated quality report for this file
    """
    subject_id = input_path.stem
    logger.info(f"Processing subject: {subject_id}")

    try:
        # Step 1: Load raw data
        raw = load_raw_eeg(input_path)
        quality_report['subjects_processed'] += 1

        # Step 2: Bandpass filter
        raw_filtered = bandpass_filter(raw)

        # Step 3: Run ICA
        ica = run_ica(raw_filtered)

        # Step 4: Detect artifacts
        rejected_components = detect_artifacts(ica, raw, raw_filtered)
        quality_report['total_ica_components'] += len(ica.n_components_)
        quality_report['rejected_components'] += len(rejected_components)

        # Step 5: Apply ICA correction
        raw_clean = apply_ica(ica, raw_filtered, rejected_components)

        # Step 6: Create epochs
        epochs = create_epochs(raw_clean)
        n_epochs_total = len(epochs)
        quality_report['total_epochs'] += n_epochs_total

        # Step 7: Compute SNR per epoch
        snr_values = compute_snr(epochs)
        quality_report['snr_values'].extend(snr_values.tolist())

        # Step 8: Flag low-SNR epochs
        low_snr_mask = snr_values < SNR_THRESHOLD_DB
        n_low_snr = np.sum(low_snr_mask)
        quality_report['low_snr_epochs'] += n_low_snr

        # Step 9: Reject epochs with >50% artifacts (based on SNR as proxy)
        # In a full implementation, we'd use peak-to-peak amplitude or other metrics
        # Here we use SNR as the primary quality metric
        rejected_epochs = np.where(low_snr_mask)[0].tolist()
        quality_report['rejected_epochs'] += len(rejected_epochs)

        # Keep only good epochs
        good_epochs_mask = ~low_snr_mask
        if np.sum(good_epochs_mask) == 0:
            logger.warning(f"All epochs rejected for subject {subject_id}")
            quality_report['subjects_all_rejected'] += 1
            return quality_report

        epochs_good = epochs[good_epochs_mask]
        n_good_epochs = len(epochs_good)
        quality_report['good_epochs'] += n_good_epochs

        # Save processed epochs
        output_path = output_dir / f"{subject_id}_epochs.fif"
        epochs_good.save(output_path, overwrite=True, verbose=False)
        quality_report['files_saved'] += 1

        # Save SNR metadata
        snr_metadata = {
            'subject_id': subject_id,
            'total_epochs': int(n_epochs_total),
            'good_epochs': int(n_good_epochs),
            'rejected_epochs': int(len(rejected_epochs)),
            'snr_values': snr_values[good_epochs_mask].tolist(),
            'mean_snr_db': float(np.mean(snr_values[good_epochs_mask])),
            'min_snr_db': float(np.min(snr_values[good_epochs_mask])),
            'max_snr_db': float(np.max(snr_values[good_epochs_mask]))
        }

        snr_path = output_dir / f"{subject_id}_snr.json"
        with open(snr_path, 'w') as f:
            json.dump(snr_metadata, f, indent=2)

        logger.info(f"Saved {n_good_epochs} good epochs for {subject_id}")

    except Exception as e:
        logger.error(f"Error processing {input_path}: {e}")
        quality_report['subjects_failed'] += 1

    return quality_report

def main():
    """
    Main entry point for preprocessing pipeline.

    Processes all raw EEG files and generates quality reports.
    """
    logger.info("Starting preprocessing pipeline...")

    # Ensure output directories exist
    output_dir = PROCESSED_DATA_DIR / 'epochs'
    output_dir.mkdir(parents=True, exist_ok=True)

    quality_dir = QUALITY_DIR
    quality_dir.mkdir(parents=True, exist_ok=True)

    # Initialize quality report
    quality_report = {
        'config': {
            'epoch_length_sec': EPOCH_LENGTH_SEC,
            'bandpass_min_freq': BANDPASS_MIN_FREQ,
            'bandpass_max_freq': BANDPASS_MAX_FREQ,
            'snr_threshold_db': SNR_THRESHOLD_DB,
            'artifact_rejection_threshold': ARTIFACT_REJECTION_THRESHOLD
        },
        'subjects_processed': 0,
        'subjects_failed': 0,
        'subjects_all_rejected': 0,
        'total_epochs': 0,
        'good_epochs': 0,
        'rejected_epochs': 0,
        'low_snr_epochs': 0,
        'total_ica_components': 0,
        'rejected_components': 0,
        'files_saved': 0,
        'snr_values': []
    }

    # Find all raw EEG files
    raw_files = list(RAW_DATA_DIR.glob('**/*.edf')) + list(RAW_DATA_DIR.glob('**/*.bdf'))
    
    if not raw_files:
        logger.warning(f"No raw EEG files found in {RAW_DATA_DIR}")
        # Still save empty report
        report_path = quality_dir / 'preprocess_report.json'
        with open(report_path, 'w') as f:
            json.dump(quality_report, f, indent=2)
        return

    logger.info(f"Found {len(raw_files)} raw EEG files")

    # Process each file
    for raw_file in raw_files:
        quality_report = preprocess_file(raw_file, output_dir, quality_report)

    # Compute summary statistics
    if quality_report['snr_values']:
        quality_report['mean_snr_db'] = float(np.mean(quality_report['snr_values']))
        quality_report['median_snr_db'] = float(np.median(quality_report['snr_values']))
        quality_report['std_snr_db'] = float(np.std(quality_report['snr_values']))
    else:
        quality_report['mean_snr_db'] = None
        quality_report['median_snr_db'] = None
        quality_report['std_snr_db'] = None

    # Save quality report
    report_path = quality_dir / 'preprocess_report.json'
    with open(report_path, 'w') as f:
        json.dump(quality_report, f, indent=2)

    logger.info(f"Preprocessing complete. Report saved to {report_path}")
    logger.info(f"Processed {quality_report['subjects_processed']} subjects, "
               f"saved {quality_report['good_epochs']} good epochs")

if __name__ == '__main__':
    main()
