import os
import sys
import yaml
import numpy as np
import mne
from pathlib import Path
import logging
from datetime import datetime
from utils.logging import log_artifact_rejection, get_logger

def load_config(config_path="code/config.yaml"):
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def stream_eeg_files(raw_dir):
    """Generator yielding (participant_id, raw) tuples."""
    raw_path = Path(raw_dir)
    if not raw_path.exists():
        raise FileNotFoundError(f"Data directory not found: {raw_dir}")
    
    # Assuming raw data is in .fif format or similar supported by MNE
    # We iterate over files to simulate streaming without loading all at once
    for file_path in raw_path.glob("*"):
        if file_path.suffix in ['.fif', '.edf', '.bdf']:
            # Extract participant ID from filename (e.g., 'sub-01_eeg.fif' -> '01')
            # Adjust logic based on actual naming convention
            pid = file_path.stem.split('_')[0].replace('sub-', '')
            try:
                raw = mne.io.read_raw_fif(file_path, preload=False)
                yield pid, raw
            except Exception:
                try:
                    raw = mne.io.read_raw_edf(file_path, preload=False)
                    yield pid, raw
                except Exception:
                    logging.warning(f"Could not read {file_path}")

def apply_bandpass_filter(raw, low_freq, high_freq):
    """Apply bandpass filter (1-40 Hz) to raw data."""
    raw_filtered = raw.copy()
    raw_filtered.filter(l_freq=low_freq, h_freq=high_freq, method='iir')
    return raw_filtered

def detect_line_noise_peak(raw):
    """Detect line noise peak in PSD."""
    psd, freqs = mne.time_frequency.psd_welch(raw, fmin=40, fmax=60)
    peak_idx = np.argmax(psd.mean(axis=0))
    return freqs[peak_idx]

def apply_notch_filter(raw, notch_freq):
    """Apply notch filter to remove line noise."""
    raw_notched = raw.copy()
    raw_notched.notch_filter(notch_freq, method='iir')
    return raw_notched

def reject_artifacts(raw, threshold, min_duration):
    """Reject epochs based on amplitude threshold and duration."""
    # Convert raw to epochs for artifact rejection
    events = mne.make_fixed_length_events(raw, duration=min_duration)
    epochs = mne.Epochs(raw, events, tmin=0, tmax=min_duration/1000, baseline=None, preload=True)
    
    rejected_epochs = []
    valid_epochs = []
    
    for i, epoch in enumerate(epochs):
        if np.max(np.abs(epoch.get_data())) > threshold:
            rejected_epochs.append(i)
        else:
            valid_epochs.append(epoch)
    
    return valid_epochs, rejected_epochs

def process_eeg_stream(raw_dir, config, output_dir):
    """Process EEG stream and save cleaned data."""
    logger = get_logger(__name__)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    low_freq = config.get('filter_low', 1)
    high_freq = config.get('filter_high', 40)
    notch_freq = config.get('notch_freq', 50)
    artifact_threshold = config.get('artifact_threshold', 100)
    min_duration = config.get('min_duration', 120)  # seconds
    
    cleaned_data = []
    exclusion_log = []
    
    for pid, raw in stream_eeg_files(raw_dir):
        try:
            # Apply bandpass filter
            raw_filtered = apply_bandpass_filter(raw, low_freq, high_freq)
            
            # Apply notch filter
            raw_notched = apply_notch_filter(raw_filtered, notch_freq)
            
            # Reject artifacts
            valid_epochs, rejected_epochs = reject_artifacts(
                raw_notched, 
                artifact_threshold, 
                min_duration
            )
            
            if not valid_epochs:
                log_artifact_rejection(pid, 'No valid epochs after rejection', datetime.now())
                continue
            
            # Concatenate valid epochs
            cleaned_raw = mne.concatenate_epochs(valid_epochs)
            
            # Save cleaned data
            out_file = output_path / f"cleaned_eeg_{pid}.fif"
            cleaned_raw.save(out_file, overwrite=True)
            cleaned_data.append(out_file)
            
        except Exception as e:
            logger.error(f"Error processing {pid}: {e}")
            exclusion_log.append({'participant_id': pid, 'reason': str(e), 'timestamp': datetime.now()})
    
    return cleaned_data, exclusion_log

def save_processed_data(cleaned_data, exclusion_log):
    """Save processed data and exclusion log."""
    # Save exclusion log
    exclusion_log_path = Path("logs/exclusion_log.csv")
    exclusion_log_path.parent.mkdir(parents=True, exist_ok=True)
    
    import pandas as pd
    if exclusion_log:
        df = pd.DataFrame(exclusion_log)
        df.to_csv(exclusion_log_path, index=False)
    
    # Save final cleaned data file
    output_path = Path("data/processed/cleaned_eeg.fif")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if cleaned_data:
        # Concatenate all cleaned files into one
        all_cleaned = []
        for file_path in cleaned_data:
            raw = mne.io.read_raw_fif(file_path, preload=False)
            all_cleaned.append(raw)
        
        final_raw = mne.concatenate_raws(all_cleaned)
        final_raw.save(output_path, overwrite=True)
    else:
        # Create empty file if no data
        with open(output_path, 'w') as f:
            f.write("")

def main():
    config = load_config()
    raw_dir = "data/raw"
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info("Starting preprocessing pipeline")
    
    try:
        cleaned_data, exclusion_log = process_eeg_stream(raw_dir, config, "data/processed")
        save_processed_data(cleaned_data, exclusion_log)
        logger.info(f"Preprocessing complete. Processed {len(cleaned_data)} participants.")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
