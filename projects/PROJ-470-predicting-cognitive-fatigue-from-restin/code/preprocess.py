"""
Preprocessing pipeline for EEG data.

Implements:
- Bandpass filtering (1-40 Hz)
- 50 Hz notch filtering
- Artifact rejection (amplitude threshold)
- Segment length validation (minimum 120 seconds)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

import numpy as np
import pandas as pd
import mne
from scipy import signal

# Import logging utility from project structure
from utils.logging import get_logger, log_artifact_rejection, save_exclusion_log_csv


def setup_logger(name: str, log_file: Optional[str] = None):
    """Setup a logger for the preprocessing pipeline."""
    logger = get_logger(name)
    if log_file:
        # Ensure log file directory exists
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    return logger


def load_config(config_path: str = "code/config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file."""
    import yaml
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def load_sample_path(manifest_path: str = "data/raw/download_manifest.json") -> str:
    """Load the sample EEG file path from the download manifest."""
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(
            f"Sample EEG file not found at {manifest_path}. "
            "Please run code/download.py first."
        )
    
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    if 'sample_file' not in manifest:
        raise KeyError(
            "Manifest missing 'sample_file' key. "
            "The download script must generate this field."
        )
    
    return manifest['sample_file']


def load_eeg_data(file_path: str) -> mne.io.Raw:
    """Load EEG data from a file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"EEG file not found: {file_path}")
    
    # Try to load as FIF file (standard for MNE)
    try:
        raw = mne.io.read_raw_fif(file_path, preload=True)
    except Exception:
        # Fallback: try other common formats
        raise ValueError(f"Unsupported file format for {file_path}. Expected .fif")
    
    return raw


def apply_filters(
    raw: mne.io.Raw,
    config: Dict[str, Any],
    logger: Optional[Any] = None
) -> mne.io.Raw:
    """
    Apply bandpass and notch filters to EEG data.
    
    Args:
        raw: Raw EEG data object
        config: Configuration dictionary with filter parameters
        logger: Logger instance for tracking operations
    
    Returns:
        Filtered raw EEG data object
    """
    if logger:
        logger.info("Starting filtering operations")
    
    # Extract filter parameters from config
    filter_low = float(config.get('filter_low', 1.0))
    filter_high = float(config.get('filter_high', 40.0))
    notch_freq = float(config.get('notch_frequency', 50.0))
    
    # Apply bandpass filter
    raw_filtered = raw.copy()
    raw_filtered.filter(
        l_freq=filter_low,
        h_freq=filter_high,
        method='iir',
        fir_design='firwin'
    )
    
    if logger:
        logger.info(f"Applied bandpass filter: {filter_low}-{filter_high} Hz")
    
    # Apply notch filter for line noise
    raw_filtered.notch_filter(
        freqs=notch_freq,
        method='iir'
    )
    
    if logger:
        logger.info(f"Applied notch filter: {notch_freq} Hz")
    
    return raw_filtered


def verify_filtering(
    raw_original: mne.io.Raw,
    raw_filtered: mne.io.Raw,
    config: Dict[str, Any],
    logger: Optional[Any] = None
) -> Dict[str, float]:
    """
    Verify that filtering has attenuated line noise.
    
    Checks that the 50Hz peak power is reduced by at least 20dB.
    
    Args:
        raw_original: Original (unfiltered) raw data
        raw_filtered: Filtered raw data
        config: Configuration dictionary
        logger: Logger instance
    
    Returns:
        Dictionary with verification results
    """
    # Compute power spectral density for both
    freqs_orig, psd_orig = raw_original.compute_psd(fmin=45, fmax=55, method='welch').get_data(return_freqs=True)
    freqs_filt, psd_filt = raw_filtered.compute_psd(fmin=45, fmax=55, method='welch').get_data(return_freqs=True)
    
    # Find peak at 50Hz
    idx_50_orig = np.argmin(np.abs(freqs_orig - 50.0))
    idx_50_filt = np.argmin(np.abs(freqs_filt - 50.0))
    
    power_orig = psd_orig[0, idx_50_orig]
    power_filt = psd_filt[0, idx_50_filt]
    
    # Calculate dB reduction
    if power_orig > 0:
        db_reduction = 10 * np.log10(power_orig / power_filt)
    else:
        db_reduction = float('inf')
    
    result = {
        'original_power_db': 10 * np.log10(power_orig) if power_orig > 0 else -np.inf,
        'filtered_power_db': 10 * np.log10(power_filt) if power_filt > 0 else -np.inf,
        'db_reduction': db_reduction,
        'threshold_db': 20.0,
        'passed': db_reduction >= 20.0
    }
    
    if logger:
        logger.info(f"Filter verification: {db_reduction:.2f} dB reduction (threshold: 20 dB)")
    
    return result


def reject_artifacts_by_amplitude(
    raw: mne.io.Raw,
    threshold_uV: int,
    logger: Optional[Any] = None
) -> List[str]:
    """
    Reject epochs that exceed amplitude threshold.
    
    Args:
        raw: Raw EEG data
        threshold_uV: Amplitude threshold in microvolts
        logger: Logger instance
    
    Returns:
        List of rejected epoch IDs
    """
    # Convert raw to epochs (assuming 2-second epochs for simplicity)
    # In a real scenario, this would use actual event markers
    events = mne.find_events(raw, stim_channel='STI 014')
    
    if len(events) == 0:
        # If no events found, create synthetic epochs for testing
        sfreq = raw.info['sfreq']
        epoch_duration = 2.0
        n_epochs = int(raw.times[-1] / epoch_duration)
        events = np.array([[i * sfreq * epoch_duration, 0, 1] for i in range(n_epochs)])
    
    epochs = mne.Epochs(
        raw,
        events,
        tmin=0,
        tmax=epoch_duration,
        baseline=None,
        preload=True
    )
    
    rejected_epochs = []
    
    # Check each epoch for amplitude threshold
    for i, epoch in enumerate(epochs):
        data = epoch.get_data()  # Shape: (n_channels, n_times)
        max_amplitude = np.max(np.abs(data))
        
        if max_amplitude > threshold_uV:
            epoch_id = f"epoch_{i}"
            rejected_epochs.append(epoch_id)
            
            if logger:
                log_artifact_rejection(
                    artifact_type="epoch",
                    artifact_id=epoch_id,
                    reason="amplitude_threshold",
                    logger=logger
                )
    
    return rejected_epochs


def validate_segment_length(
    raw: mne.io.Raw,
    min_duration_seconds: int,
    logger: Optional[Any] = None
) -> bool:
    """
    Validate that the segment duration meets minimum requirements.
    
    Args:
        raw: Raw EEG data
        min_duration_seconds: Minimum required duration in seconds
        logger: Logger instance
    
    Returns:
        True if segment is valid, False otherwise
    """
    duration = raw.times[-1]
    
    if duration < min_duration_seconds:
        if logger:
            log_artifact_rejection(
                artifact_type="segment",
                artifact_id=raw.info['subject_info'].get('his_id', 'unknown'),
                reason="segment_too_short",
                logger=logger
            )
        return False
    
    return True


def preprocess_eeg(
    input_path: str,
    output_path: str,
    config: Dict[str, Any],
    logger: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Main preprocessing pipeline.
    
    Steps:
    1. Load raw EEG data
    2. Validate segment length
    3. Apply filters (bandpass + notch)
    4. Reject artifacts by amplitude
    5. Save cleaned data
    
    Args:
        input_path: Path to input EEG file
        output_path: Path to save cleaned EEG file
        config: Configuration dictionary
        logger: Logger instance
    
    Returns:
        Dictionary with processing results
    """
    results = {
        'input_file': input_path,
        'output_file': output_path,
        'success': False,
        'warnings': []
    }
    
    # Load data
    raw = load_eeg_data(input_path)
    results['original_duration'] = raw.times[-1]
    
    # Validate segment length
    min_duration = config.get('min_segment_duration', 120)
    if not validate_segment_length(raw, min_duration, logger):
        results['warnings'].append(f"Segment too short: {raw.times[-1]:.2f}s < {min_duration}s")
        # We do not exit here; we log and continue to allow analysis of available data
        # but mark the segment as potentially invalid for certain analyses
    
    # Apply filters
    raw_filtered = apply_filters(raw, config, logger)
    
    # Verify filtering
    verification = verify_filtering(raw, raw_filtered, config, logger)
    results['filter_verification'] = verification
    
    # Reject artifacts
    rejected_epochs = reject_artifacts_by_amplitude(
        raw_filtered,
        config.get('artifact_threshold_uV', 100),
        logger
    )
    results['rejected_epochs'] = rejected_epochs
    
    # Save cleaned data
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    raw_filtered.save(output_path, overwrite=True)
    results['success'] = True
    
    return results


def main():
    """Main entry point for the preprocessing script."""
    parser = argparse.ArgumentParser(description='Preprocess EEG data')
    parser.add_argument('--config', type=str, default='code/config.yaml', help='Path to config file')
    parser.add_argument('--manifest', type=str, default='data/raw/download_manifest.json', help='Path to download manifest')
    parser.add_argument('--output', type=str, default='data/processed/cleaned_eeg.fif', help='Output file path')
    args = parser.parse_args()
    
    # Setup logger
    logger = setup_logger("preprocess")
    
    # Load config
    config = load_config(args.config)
    
    # Load sample path from manifest
    try:
        input_path = load_sample_path(args.manifest)
    except (FileNotFoundError, KeyError) as e:
        logger.error(str(e))
        sys.exit(1)
    
    # Run preprocessing
    results = preprocess_eeg(input_path, args.output, config, logger)
    
    # Log results
    if results['success']:
        logger.info(f"Preprocessing complete. Output saved to {args.output}")
    else:
        logger.error("Preprocessing failed")
        sys.exit(1)
    
    # Print summary
    print(json.dumps(results, indent=2, default=str))


if __name__ == '__main__':
    main()
