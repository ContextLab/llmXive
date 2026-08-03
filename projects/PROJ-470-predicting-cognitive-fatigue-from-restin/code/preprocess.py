"""
Preprocessing module for EEG data.
Applies bandpass filter, notch filter, and artifact rejection.
"""
import os
import sys
import yaml
import logging
import numpy as np
import mne
from pathlib import Path
from datetime import datetime

# Import local utilities
try:
    from utils.logging import get_logger, log_artifact_rejection, save_exclusion_log_csv
except ImportError:
    logging.basicConfig(level=logging.INFO)
    def get_logger(name):
        return logging.getLogger(name)

def load_config(config_path="code/config.yaml"):
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def setup_logger(name):
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

def stream_eeg_files(input_dir):
    """Generator to yield EEG file paths."""
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.endswith(('.fif', '.edf', '.bdf')):
                yield os.path.join(root, file)

def apply_bandpass_filter(raw, low, high):
    """Apply bandpass filter."""
    raw.filter(low, high, method='iir', phase='forward')
    return raw

def detect_line_noise_peak(raw):
    """Detect line noise peak (simplified)."""
    # In a real implementation, use Welch's method to find peak
    return 50 # Default fallback

def apply_notch_filter(raw, freq):
    """Apply notch filter to remove line noise."""
    raw.notch_filter(freq, method='iir')
    return raw

def reject_artifacts(raw, threshold):
    """
    Reject epochs/segments with amplitude > threshold.
    Returns a list of rejected segment IDs or counts.
    """
    # Simplified logic for skeleton
    data = raw.get_data()
    # Check max amplitude across all channels and time
    max_amp = np.max(np.abs(data))
    rejected = max_amp > threshold
    return rejected

def process_eeg_stream(files, config, logger):
    """Process a stream of EEG files."""
    processed_data = []
    for fpath in files:
        try:
            raw = mne.io.read_raw_fif(fpath, preload=False)
            # Apply filters
            raw = apply_bandpass_filter(raw, config['filter_low'], config['filter_high'])
            raw = apply_notch_filter(raw, config['notch_freq'])
            
            # Artifact rejection
            if reject_artifacts(raw, config['artifact_threshold']):
                logger.warning(f"Artifact detected in {fpath}, skipping.")
                continue
            
            processed_data.append(raw)
        except Exception as e:
            logger.error(f"Error processing {fpath}: {e}")
    return processed_data

def save_processed_data(processed_data, output_path):
    """Save processed data to FIF file."""
    if not processed_data:
        raise FileNotFoundError("No processed data to save.")
    # Concatenate or save first for demo
    # In real implementation, handle multiple participants
    combined = processed_data[0] # Placeholder
    combined.save(output_path, overwrite=True)

def main():
    config = load_config()
    logger = setup_logger("preprocess")
    logger.info("Starting preprocessing pipeline.")

    input_dir = "data/raw"
    if not os.path.exists(input_dir):
        logger.error(f"Input directory not found: {input_dir}")
        sys.exit(1)

    files = list(stream_eeg_files(input_dir))
    if not files:
        logger.warning("No EEG files found in input directory.")
        # Create empty output to allow downstream to fail gracefully or handle empty case
        # But T011 requires real data. If no files, we exit.
        sys.exit(1)

    processed = process_eeg_stream(files, config, logger)
    
    output_dir = "data/processed"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "cleaned_eeg.fif")
    
    try:
        save_processed_data(processed, output_path)
        logger.info(f"Processed data saved to {output_path}")
    except Exception as e:
        logger.error(f"Failed to save processed data: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
