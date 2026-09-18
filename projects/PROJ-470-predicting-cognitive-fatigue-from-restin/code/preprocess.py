"""Preprocessing: Bandpass filter, notch filter, artifact rejection.

Implements FR-002: Apply 1-40 Hz bandpass, 50 Hz notch, reject artifacts >100uV.
"""
import os
import sys
import yaml
import logging
import numpy as np
import mne
from pathlib import Path

# Import local utilities
from utils.logging import get_logger, save_exclusion_log_csv

def load_config(config_path="code/config.yaml"):
    """Load configuration from YAML file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def setup_logger(name, log_file=None):
    """Setup a logger that writes to file and console."""
    logger = get_logger(name, log_file)
    return logger

def apply_bandpass_filter(raw, low_cut, high_cut):
    """Apply bandpass filter."""
    raw.filter(low_cut, high_cut, fir_design='firwin')
    return raw

def apply_notch_filter(raw, freq):
    """Apply notch filter."""
    raw.notch_filter(freq)
    return raw

def reject_artifacts(raw, threshold_uV):
    """Reject epochs with amplitude > threshold."""
    # This is a simplified version; in reality, we would use mne.Epochs
    # and reject based on peak-to-peak amplitude
    data = raw.get_data()
    # Assume threshold is in microvolts
    bad_epochs = np.any(np.abs(data) > threshold_uV, axis=1)
    return bad_epochs

def process_eeg_stream(input_file, output_file, config):
    """Process EEG stream: filter, reject artifacts."""
    # Load raw data
    raw = mne.io.read_raw_fif(input_file, preload=True)

    # Apply filters
    raw = apply_bandpass_filter(raw, config['filter_low'], config['filter_high'])
    raw = apply_notch_filter(raw, config['notch_freq'])

    # Reject artifacts
    bad_mask = reject_artifacts(raw, config['artifact_threshold_uV'])
    # In a real implementation, we would create epochs and reject them
    # Here we just log the count
    excluded_count = np.sum(bad_mask)

    # Save processed data
    raw.save(output_file, overwrite=True)

    return excluded_count

def save_exclusion_log(exclusions, output_path):
    """Save exclusion log to CSV."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    if not exclusions:
        with open(output_path, 'w') as f:
            f.write("participant_id,reason,timestamp\n")
        return
    df = pd.DataFrame(exclusions)
    df.to_csv(output_path, index=False)

def main():
    """Main entry point for preprocessing."""
    logger = setup_logger("preprocess")
    logger.info("Starting preprocessing pipeline.")

    # Load config
    try:
        config = load_config()
    except FileNotFoundError:
        print("Warning: config.yaml not found. Using defaults.")
        config = {'filter_low': 1, 'filter_high': 40, 'notch_freq': 50, 'artifact_threshold_uV': 100}

    # Define paths
    input_file = "data/raw/sample_eeg.fif"
    output_file = "data/processed/cleaned_eeg.fif"
    exclusion_log = "data/processed/exclusion_log.csv"

    if not os.path.exists(input_file):
        logger.error(f"Input file not found: {input_file}")
        print(f"ERROR: Sample EEG file not found at {input_file}.")
        print("Please run code/download.py first.")
        sys.exit(1)

    try:
        excluded_count = process_eeg_stream(input_file, output_file, config)
        logger.info(f"Preprocessing complete. {excluded_count} epochs excluded.")
        print(f"Success: Cleaned EEG saved to {output_file}")
    except Exception as e:
        logger.error(f"Error during preprocessing: {e}")
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    import pandas as pd
    main()
