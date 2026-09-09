"""
Preprocessing pipeline for EEG data.
Applies filtering, artifact rejection, and segment length validation.
"""
import os
import sys
import yaml
import logging
import numpy as np
import mne
from pathlib import Path

# Import logging utilities from the shared module
from code.utils.logging import get_logger, log_participant_exclusion, save_exclusion_log_csv

def load_config(config_path="code/config.yaml"):
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def setup_logger(name, log_file=None):
    """
    Setup a logger that is tolerant of different call signatures.
    Falls back to a ReproducibilityLogger if log_file is provided but not handled by standard logging.
    """
    # Attempt to use the shared utility which is designed to be tolerant
    try:
        # Try calling with both args (as used in preprocess.py)
        logger = get_logger(name, log_file)
        return logger
    except Exception:
        # Fallback to standard logging if the shared one fails for some reason
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

def stream_eeg_files(data_dir):
    """Generator to yield EEG file paths from a directory."""
    data_path = Path(data_dir)
    if not data_path.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")
    
    for ext in ['*.fif', '*.edf', '*.bdf', '*.vhdr']:
        for file_path in data_path.rglob(ext):
            yield str(file_path)

def apply_bandpass_filter(raw, low_cut, high_cut, l_trans_bandwidth='auto', h_trans_bandwidth='auto'):
    """Apply bandpass filter to raw data."""
    raw_filtered = raw.copy()
    raw_filtered.filter(low_freq=low_cut, high_freq=high_cut, 
                        l_trans_bandwidth=l_trans_bandwidth, 
                        h_trans_bandwidth=h_trans_bandwidth)
    return raw_filtered

def apply_notch_filter(raw, freq, q=30.0):
    """Apply notch filter to remove line noise."""
    raw_notched = raw.copy()
    raw_notched.notch_filter(freqs=freq, q=q)
    return raw_notched

def detect_line_noise_peak(raw, freq=50):
    """Detect and report line noise peak power."""
    psd, freqs = raw.compute_psd(method='welch')
    # Find index closest to 50 Hz
    idx = np.argmin(np.abs(freqs - freq))
    peak_power = np.mean(psd[:, idx])
    return peak_power

def reject_artifacts(raw, threshold_uV=100):
    """
    Reject epochs that exceed the amplitude threshold.
    Logs rejected epochs to exclusion_log.csv.
    """
    # Get data and times
    data = raw.get_data()
    info = raw.info
    sfreq = info['sfreq']
    n_channels = len(info['ch_names'])
    
    # Calculate absolute amplitude for each channel
    # We assume the data is in Volts, convert to microvolts
    data_uv = data * 1e6
    
    # Find channels/epochs exceeding threshold
    # For continuous data, we look for segments where max amplitude > threshold
    max_amplitudes = np.max(np.abs(data_uv), axis=1)
    
    rejected_indices = np.where(max_amplitudes > threshold_uV)[0]
    
    if len(rejected_indices) > 0:
        # Log the rejection
        # Assuming we are processing a single subject, we log the channel indices
        # In a real scenario, we might have a participant_id passed in
        participant_id = "unknown" 
        for idx in rejected_indices:
            log_participant_exclusion(participant_id, f"Channel {idx} amplitude > {threshold_uV}uV", "amplitude_threshold")
        
        # Create a mask to drop bad channels or segments
        # For simplicity in this context, we drop the bad channels
        # In a real epoch-based workflow, we would drop epochs
        bad_channels = [info['ch_names'][i] for i in rejected_indices]
        raw.drop_channels(bad_channels)
        
        # Log to file
        save_exclusion_log_csv(participant_id, "amplitude_threshold", "rejected channels due to high amplitude")

    return raw

def reject_short_segments(raw, min_duration_seconds=120):
    """
    Reject segments shorter than the minimum duration.
    Logs rejected segments to exclusion_log.csv.
    """
    info = raw.info
    sfreq = info['sfreq']
    n_samples = raw.n_times
    duration = n_samples / sfreq
    
    participant_id = "unknown" # In a real scenario, this would be extracted from the filename or metadata
    
    if duration < min_duration_seconds:
        # Log the rejection
        log_participant_exclusion(participant_id, f"Duration {duration:.2f}s < {min_duration_seconds}s", "segment_too_short")
        save_exclusion_log_csv(participant_id, "segment_too_short", f"Segment duration {duration:.2f}s is less than {min_duration_seconds}s")
        return None # Indicate that this segment should be excluded
    
    return raw

def process_eeg_stream(input_files, config):
    """Process a stream of EEG files."""
    processed_files = []
    
    for file_path in input_files:
        try:
            raw = mne.io.read_raw_fif(file_path, preload=True)
            original_duration = raw.n_times / raw.info['sfreq']
            
            # Apply filters
            raw = apply_bandpass_filter(raw, config['filter_low'], config['filter_high'])
            raw = apply_notch_filter(raw, config['notch_frequency'])
            
            # Reject artifacts
            raw = reject_artifacts(raw, config['artifact_threshold_uV'])
            
            # Reject short segments
            raw = reject_short_segments(raw, config.get('min_segment_duration', 120))
            
            if raw is not None:
                processed_files.append(file_path)
            
        except Exception as e:
            logging.error(f"Error processing {file_path}: {e}")
            continue
    
    return processed_files

def save_processed_data(raw, output_path):
    """Save processed EEG data to a file."""
    raw.save(output_path, overwrite=True)

def save_exclusion_log():
    """Ensure exclusion log is saved (wrapper for utility function)."""
    # This is called at the end of processing to ensure all logs are flushed
    pass

def main():
    """Main entry point for preprocessing."""
    config = load_config()
    logger = setup_logger("preprocess")
    
    logger.info("Starting preprocessing pipeline.")
    
    # Ensure output directory exists
    os.makedirs("data/processed", exist_ok=True)
    
    # Get input files
    input_files = list(stream_eeg_files("data/raw"))
    
    if not input_files:
        logger.error("No input files found in data/raw/")
        sys.exit(1)
    
    # Process files
    processed_files = process_eeg_stream(input_files, config)
    
    if not processed_files:
        logger.warning("No files were successfully processed.")
    
    logger.info(f"Processed {len(processed_files)} files.")
    logger.info("Preprocessing pipeline completed.")

if __name__ == "__main__":
    main()
