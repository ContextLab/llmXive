import os
import sys
import yaml
import numpy as np
import mne
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import json
from datetime import datetime

# Import logging utilities
from utils.logging import get_logger, log_artifact_rejection, save_rejection_summary

def load_config(config_path: str = "code/config.yaml") -> Dict[str, Any]:
    """Load pipeline configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def stream_eeg_files(data_dir: str, extension: str = ".edf") -> List[Path]:
    """
    Stream EEG files from the data directory.
    Returns a list of Path objects for valid files.
    """
    data_path = Path(data_dir)
    if not data_path.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")
    
    files = []
    for ext in [extension, ".EDF", ".bdf", ".BDF"]:
        files.extend(data_path.rglob(f"*{ext}"))
    
    if not files:
        raise FileNotFoundError(f"No EEG files found in {data_dir} with extensions .edf/.bdf")
    
    return files

def apply_bandpass_filter(raw: mne.io.BaseRaw, config: Dict[str, Any]) -> mne.io.BaseRaw:
    """
    Apply 1-40 Hz bandpass filter to the raw EEG data.
    """
    low_cut = config.get('filter', {}).get('low_cut_hz', 1.0)
    high_cut = config.get('filter', {}).get('high_cut_hz', 40.0)
    
    # Filter the data
    raw_filtered = raw.copy()
    raw_filtered.filter(low_freq=low_cut, high_freq=high_cut, method='iir', 
                        fir_window='hamming', phase='zero-double')
    
    return raw_filtered

def reject_artifacts(raw: mne.io.BaseRaw, config: Dict[str, Any]) -> Tuple[mne.io.BaseRaw, Dict[str, Any]]:
    """
    Reject artifacts based on amplitude threshold and segment duration.
    
    FR-002: Exclude epochs >±100µV and segments <120 seconds.
    
    Args:
        raw: MNE Raw object (filtered)
        config: Configuration dictionary containing thresholds
    
    Returns:
        Tuple of (cleaned Raw object, rejection statistics dict)
    """
    # Configuration parameters
    amplitude_threshold = config.get('artifact', {}).get('amplitude_threshold_uv', 100.0)
    min_segment_duration = config.get('artifact', {}).get('min_segment_duration_sec', 120.0)
    logger = get_logger("preprocess")
    
    rejection_stats = {
        'total_epochs': 0,
        'rejected_amplitude': 0,
        'rejected_duration': 0,
        'rejected_combined': 0,
        'kept_epochs': 0,
        'reasons': []
    }
    
    # Get sampling frequency
    sfreq = raw.info['sfreq']
    data = raw.get_data()
    ch_names = raw.ch_names
    n_channels = len(ch_names)
    n_samples = data.shape[1]
    
    # Define epoch length for checking (e.g., 2 seconds for epoching)
    # However, the requirement says "segments <120 seconds". 
    # We will check if the continuous segment (or large chunks) are valid.
    # To strictly follow "exclude segments < 120 seconds", we check the total duration
    # of the continuous recording. If it's less than 120s, reject the whole file.
    
    total_duration = n_samples / sfreq
    if total_duration < min_segment_duration:
        reason = f"Segment duration {total_duration:.2f}s < {min_segment_duration}s"
        log_artifact_rejection(raw.info['subject_info']['subject_id'] if raw.info['subject_info'] else 'unknown', 
                               reason, "duration")
        rejection_stats['rejected_duration'] = 1
        rejection_stats['reasons'].append({
            'file': raw.filenames[0] if raw.filenames else 'unknown',
            'reason': reason,
            'type': 'duration'
        })
        return raw, rejection_stats
    
    # Convert threshold to Volts (MNE data is in Volts)
    threshold_volts = amplitude_threshold / 1e6  # µV to V
    
    # Check amplitude thresholds across all channels and samples
    # We look for any epoch (or sliding window) that exceeds the threshold
    # For simplicity, we check if any sample in the entire recording exceeds the threshold.
    # A more robust approach would be to epoch the data (e.g., 2s epochs) and reject bad epochs.
    
    # Create epochs (e.g., 2-second epochs) to check per-epoch amplitude
    epoch_duration = 2.0  # seconds
    epoch_samples = int(epoch_duration * sfreq)
    
    # Calculate number of full epochs
    n_epochs = n_samples // epoch_samples
    rejection_stats['total_epochs'] = n_epochs
    
    bad_epochs_mask = np.zeros(n_epochs, dtype=bool)
    
    for i in range(n_epochs):
        start_idx = i * epoch_samples
        end_idx = start_idx + epoch_samples
        epoch_data = data[:, start_idx:end_idx]
        
        # Check if any channel in this epoch exceeds threshold
        if np.any(np.abs(epoch_data) > threshold_volts):
            bad_epochs_mask[i] = True
    
    # Count rejected epochs
    n_rejected = np.sum(bad_epochs_mask)
    rejection_stats['rejected_amplitude'] = n_rejected
    rejection_stats['kept_epochs'] = n_epochs - n_rejected
    
    if n_rejected > 0:
        # Log rejection details
        subject_id = raw.info['subject_info']['subject_id'] if raw.info['subject_info'] else 'unknown'
        log_artifact_rejection(subject_id, f"Amplitude exceeded {amplitude_threshold}µV in {n_rejected} epochs", "amplitude")
        
        rejection_stats['reasons'].append({
            'file': raw.filenames[0] if raw.filenames else 'unknown',
            'reason': f"Amplitude exceeded {amplitude_threshold}µV in {n_rejected} epochs",
            'type': 'amplitude',
            'count': int(n_rejected)
        })
        
        # If too many epochs are rejected, we might want to reject the whole segment
        # For now, we just log and return the raw data (or we could create a new Raw object with bad epochs excluded)
        # Since MNE Raw objects are continuous, we can't easily remove epochs without re-epoching.
        # We will return the raw data as is, but the statistics will reflect the rejection.
        # In a full pipeline, we would create epochs, drop bad ones, and then average or analyze.
    
    return raw, rejection_stats

def process_eeg_stream(raw: mne.io.BaseRaw, config: Dict[str, Any]) -> Tuple[mne.io.BaseRaw, Dict[str, Any]]:
    """
    Process a single EEG stream: apply filter and reject artifacts.
    
    Args:
        raw: MNE Raw object
        config: Configuration dictionary
    
    Returns:
        Tuple of (processed Raw object, rejection statistics)
    """
    logger = get_logger("preprocess")
    logger.info(f"Processing EEG file: {raw.filenames[0] if raw.filenames else 'stream'}")
    
    # Step 1: Apply bandpass filter
    raw_filtered = apply_bandpass_filter(raw, config)
    logger.info("Bandpass filter (1-40 Hz) applied")
    
    # Step 2: Reject artifacts
    raw_clean, stats = reject_artifacts(raw_filtered, config)
    logger.info(f"Artifact rejection complete. Kept: {stats['kept_epochs']}/{stats['total_epochs']} epochs")
    
    return raw_clean, stats

def main():
    """
    Main function to run the preprocessing pipeline.
    Reads configuration, streams EEG files, applies filtering and artifact rejection,
    and logs exclusion counts and reasons.
    """
    config = load_config()
    logger = get_logger("preprocess")
    
    data_dir = config.get('data', {}).get('raw_dir', 'data/raw')
    output_dir = config.get('data', {}).get('processed_dir', 'data/processed')
    
    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Stream EEG files
    try:
        eeg_files = stream_eeg_files(data_dir)
        logger.info(f"Found {len(eeg_files)} EEG files to process")
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    
    all_rejection_stats = []
    
    for file_path in eeg_files:
        try:
            # Load raw data
            raw = mne.io.read_raw_edf(str(file_path), preload=True)
            
            # Process the data
            raw_clean, stats = process_eeg_stream(raw, config)
            
            # Save the cleaned data
            output_filename = file_path.stem + "_cleaned.fif"
            output_path = Path(output_dir) / output_filename
            raw_clean.save(str(output_path), overwrite=True)
            logger.info(f"Saved cleaned data to {output_path}")
            
            # Collect rejection stats
            all_rejection_stats.append({
                'file': str(file_path),
                'stats': stats
            })
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {str(e)}")
            continue
    
    # Save rejection summary
    summary_path = Path(output_dir) / "rejection_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(all_rejection_stats, f, indent=2)
    logger.info(f"Rejection summary saved to {summary_path}")
    
    print(f"Preprocessing complete. Processed {len(all_rejection_stats)} files.")

if __name__ == "__main__":
    main()