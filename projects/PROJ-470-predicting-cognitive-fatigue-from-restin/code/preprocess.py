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

def reject_artifacts(raw, threshold_uV, min_duration_s, logger, participant_id):
    """
    Reject epochs/segments with amplitude > threshold or duration < min_duration.
    Returns True if the segment should be REJECTED (excluded).
    Logs the rejection reason to the exclusion log.
    """
    data = raw.get_data()
    sfreq = raw.info['sfreq']
    
    # 1. Check Amplitude Threshold (FR-002)
    # Max absolute amplitude across all channels and time points
    max_amp = np.max(np.abs(data))
    if max_amp > threshold_uV:
        logger.warning(f"Artifact detected in {participant_id}: amplitude {max_amp:.2f}uV > {threshold_uV}uV")
        log_artifact_rejection(
            participant_id=participant_id,
            reason=f"amplitude > {threshold_uV}uV",
            timestamp=datetime.now().isoformat()
        )
        return True

    # 2. Check Segment Duration (FR-002 Edge Cases)
    duration_s = raw.times[-1] - raw.times[0]
    if duration_s < min_duration_s:
        logger.warning(f"Segment too short in {participant_id}: {duration_s:.2f}s < {min_duration_s}s")
        log_artifact_rejection(
            participant_id=participant_id,
            reason=f"segment < {min_duration_s}s",
            timestamp=datetime.now().isoformat()
        )
        return True

    return False

def process_eeg_stream(files, config, logger):
    """Process a stream of EEG files."""
    processed_data = []
    # Extract config values with defaults
    threshold_uV = config.get('artifact_threshold_uV', 100)
    min_duration_s = config.get('min_segment_duration_s', 120)
    
    for fpath in files:
        try:
            # Check if file exists before loading
            if not os.path.exists(fpath):
                logger.error(f"File not found: {fpath}")
                continue

            raw = mne.io.read_raw_fif(fpath, preload=True)
            
            # Apply bandpass filter (1-40 Hz)
            raw = apply_bandpass_filter(raw, config['filter_low'], config['filter_high'])
            
            # Apply notch filter (line noise removal)
            # Read notch frequency from config, default to 50 Hz
            # Note: config key is 'notch_frequency' per T005/T009 spec
            notch_freq = config.get('notch_frequency', 50)
            raw = apply_notch_filter(raw, notch_freq)
            
            # Artifact rejection
            participant_id = Path(fpath).stem
            if reject_artifacts(raw, threshold_uV, min_duration_s, logger, participant_id):
                # If rejected, we do NOT add to processed_data
                continue
            
            processed_data.append(raw)
        except FileNotFoundError as e:
            logger.error(f"File not found: {fpath}. Error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error processing {fpath}: {e}")
            continue
    return processed_data

def save_processed_data(processed_data, output_path):
    """Save processed data to FIF file."""
    if not processed_data:
        raise FileNotFoundError("No processed data to save.")
    
    # For the first file, save it directly
    # In a real implementation, we might concatenate or handle multiple participants
    first_raw = processed_data[0]
    first_raw.save(output_path, overwrite=True)

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
        sys.exit(1)

    processed = process_eeg_stream(files, config, logger)
    
    output_dir = "data/processed"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "cleaned_eeg.fif")
    
    try:
        save_processed_data(processed, output_path)
        logger.info(f"Processed data saved to {output_path}")
    except FileNotFoundError as e:
        logger.error(f"Input file error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to save processed data: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
