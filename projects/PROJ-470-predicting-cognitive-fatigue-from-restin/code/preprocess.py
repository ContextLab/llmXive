import os
import sys
import yaml
import logging
import numpy as np
import mne
from pathlib import Path
from datetime import datetime

from utils.logging import get_logger, log_artifact_rejection, save_exclusion_log_csv

def load_config(config_path="code/config.yaml"):
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def setup_logger(name, log_file='logs/preprocess.log'):
    """Set up logging configuration."""
    Path("logs").mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.INFO)
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        logger.addHandler(fh)
        logger.addHandler(ch)
    
    return logger

def stream_eeg_files(data_dir):
    """Generator to yield EEG files from the raw data directory."""
    raw_path = Path(data_dir)
    if not raw_path.exists():
        return
    
    for ext in ['*.fif', '*.edf', '*.bdf', '*.vhdr']:
        for file_path in raw_path.glob(ext):
            yield file_path

def apply_bandpass_filter(raw, low_cut, high_cut, logger):
    """Apply bandpass filter to the raw data."""
    logger.info(f"Applying bandpass filter: {low_cut}-{high_cut} Hz")
    raw.filter(low_freq=low_cut, high_freq=high_cut, n_jobs=1)
    return raw

def detect_line_noise_peak(raw, logger):
    """Detect line noise peak in the spectrum."""
    psd, freqs = mne.time_frequency.psd_welch(raw, fmin=45, fmax=55, n_fft=256)
    peak_idx = np.argmax(np.mean(psd, axis=0))
    return freqs[peak_idx]

def apply_notch_filter(raw, notch_freq, logger):
    """Apply notch filter to remove line noise."""
    logger.info(f"Applying notch filter at {notch_freq} Hz")
    raw.notch_filter(freqs=[notch_freq], n_jobs=1)
    return raw

def reject_artifacts(raw, amplitude_threshold, min_duration, logger, participant_id):
    """
    Reject epochs/segments based on amplitude and duration.
    
    Args:
        raw: MNE Raw object
        amplitude_threshold: Threshold in microvolts (default 100)
        min_duration: Minimum duration in seconds (default 120)
        logger: Logger instance
        participant_id: ID of the participant for logging
    
    Returns:
        tuple: (cleaned_raw, exclusion_reasons)
    """
    exclusion_reasons = []
    current_time = datetime.now().isoformat()
    
    # Check duration
    duration = raw.times[-1] - raw.times[0]
    if duration < min_duration:
        reason = f"segment < {min_duration}s"
        exclusion_reasons.append({
            'participant_id': participant_id,
            'reason': reason,
            'timestamp': current_time
        })
        logger.warning(f"Participant {participant_id} excluded: {reason}")
        return None, exclusion_reasons
    
    # Check amplitude
    data = raw.get_data()
    max_amplitude = np.max(np.abs(data))
    if max_amplitude > amplitude_threshold:
        reason = f"amplitude > {amplitude_threshold}uV"
        exclusion_reasons.append({
            'participant_id': participant_id,
            'reason': reason,
            'timestamp': current_time
        })
        logger.warning(f"Participant {participant_id} excluded: {reason}")
        return None, exclusion_reasons
    
    return raw, exclusion_reasons

def process_eeg_stream(config, logger):
    """Process the stream of EEG files."""
    data_dir = config.get('data_raw_dir', 'data/raw')
    output_dir = config.get('data_processed_dir', 'data/processed')
    amplitude_threshold = config.get('artifact_threshold', 100)
    min_duration = 120
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    all_exclusions = []
    processed_count = 0
    excluded_count = 0
    
    for file_path in stream_eeg_files(data_dir):
        try:
            # Extract participant ID from filename
            participant_id = file_path.stem
            logger.info(f"Processing {participant_id} from {file_path}")
            
            # Load raw data
            raw = mne.io.read_raw_fif(file_path, preload=False)
            if file_path.suffix == '.edf' or file_path.suffix == '.bdf':
                raw = mne.io.read_raw_edf(file_path, preload=False)
            
            # Apply filters
            low_cut = config.get('filter_low', 1)
            high_cut = config.get('filter_high', 40)
            raw = apply_bandpass_filter(raw, low_cut, high_cut, logger)
            
            # Apply notch filter
            notch_freq = config.get('notch_frequency', 50)
            raw = apply_notch_filter(raw, notch_freq, logger)
            
            # Reject artifacts
            cleaned_raw, exclusions = reject_artifacts(
                raw, 
                amplitude_threshold, 
                min_duration, 
                logger, 
                participant_id
            )
            
            all_exclusions.extend(exclusions)
            
            if cleaned_raw is None:
                excluded_count += 1
                continue
            
            # Save processed data
            output_path = Path(output_dir) / f"{participant_id}_cleaned.fif"
            cleaned_raw.save(output_path, overwrite=True)
            processed_count += 1
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            continue
    
    # Save exclusion log
    if all_exclusions:
        save_exclusion_log_csv(all_exclusions, 'logs/exclusion_log.csv')
        logger.info(f"Saved exclusion log with {len(all_exclusions)} entries")
    
    logger.info(f"Processing complete. Processed: {processed_count}, Excluded: {excluded_count}")
    return processed_count, excluded_count

def save_processed_data(raw, output_path):
    """Save processed raw data to FIF file."""
    raw.save(output_path, overwrite=True)

def main():
    """Main entry point for preprocessing pipeline."""
    logger = setup_logger('preprocess')
    logger.info("Starting preprocessing pipeline")
    
    try:
        config = load_config()
        process_eeg_stream(config, logger)
        logger.info("Preprocessing pipeline completed successfully")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
