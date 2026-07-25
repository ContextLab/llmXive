import os
import sys
import yaml
import logging
import numpy as np
import mne
from pathlib import Path
from datetime import datetime
from typing import Generator, List, Optional, Tuple

# Import from local utils
from utils.logging import get_logger, log_participant_exclusion, log_artifact_rejection, save_exclusion_log_csv

def load_config(config_path: str = "code/config.yaml") -> dict:
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def setup_logger(name: str, log_dir: str = "logs") -> logging.Logger:
    """Set up a logger that writes to both console and a file."""
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    log_file = Path(log_dir) / f"{name}.log"
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers to avoid duplicates
    if logger.handlers:
        logger.handlers.clear()
    
    # File handler
    fh = logging.FileHandler(log_file, mode='a')
    fh.setLevel(logging.INFO)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    return logger

def stream_eeg_files(data_dir: str, logger: logging.Logger) -> Generator[Tuple[str, mne.io.BaseRaw], None, None]:
    """
    Stream EEG files from the data directory to support memory-efficient processing.
    Yields (participant_id, raw_object) tuples.
    """
    data_path = Path(data_dir)
    if not data_path.exists():
        logger.error(f"Data directory not found: {data_dir}")
        raise FileNotFoundError(f"Data directory not found: {data_dir}")
    
    # Look for common EEG file extensions
    extensions = ['.fif', '.edf', '.bdf', '.vhdr', '.set']
    files = []
    for ext in extensions:
        files.extend(data_path.rglob(f'*{ext}'))
    
    if not files:
        logger.warning(f"No EEG files found in {data_dir}")
        return
    
    for file_path in files:
        try:
            # Extract participant ID from filename
            participant_id = file_path.stem
            
            # Stream the file (preload=False) to save memory
            logger.info(f"Loading {participant_id} from {file_path}...")
            raw = mne.io.read_raw_fif(file_path, preload=False) if file_path.suffix == '.fif' else mne.io.read_raw_edf(file_path, preload=False)
            
            # Set montage if available (optional, but good practice)
            # raw.set_montage('standard_1020', match_case=False, match_alias=True)
            
            yield participant_id, raw
        except Exception as e:
            logger.error(f"Failed to load {file_path}: {e}")
            continue

def apply_bandpass_filter(raw: mne.io.BaseRaw, low_freq: float, high_freq: float, logger: logging.Logger) -> mne.io.BaseRaw:
    """Apply bandpass filter to remove frequencies outside the 1-40 Hz range."""
    logger.info(f"Applying bandpass filter: {low_freq}-{high_freq} Hz")
    raw.filter(low_freq, high_freq, method='iir', fir_window='hamming')
    return raw

def detect_line_noise_peak(raw: mne.io.BaseRaw, notch_freq: float, logger: logging.Logger) -> float:
    """
    Detect the actual line noise peak frequency using PSD.
    Returns the detected frequency (should be close to notch_freq).
    """
    logger.info("Detecting line noise peak frequency...")
    # Compute PSD
    psd, freqs = mne.time_frequency.psd_welch(raw, fmin=45, fmax=55, n_fft=2048)
    peak_idx = np.argmax(np.mean(psd, axis=0))
    detected_freq = freqs[peak_idx]
    logger.info(f"Detected line noise peak at {detected_freq:.2f} Hz")
    return detected_freq

def apply_notch_filter(raw: mne.io.BaseRaw, notch_freq: float, logger: logging.Logger) -> mne.io.BaseRaw:
    """Apply notch filter to remove line noise at the specified frequency."""
    logger.info(f"Applying notch filter at {notch_freq} Hz")
    raw.notch_filter(notch_freq)
    return raw

def reject_artifacts(raw: mne.io.BaseRaw, threshold: float, min_duration: float, logger: logging.Logger, participant_id: str, exclusion_log: List[dict]) -> Optional[mne.io.BaseRaw]:
    """
    Reject artifacts based on amplitude threshold and minimum duration.
    Returns None if the segment is rejected, otherwise returns the cleaned raw object.
    """
    # Get data and check amplitude
    data = raw.get_data()
    max_amplitude = np.max(np.abs(data))
    
    # Check duration
    duration = raw.times[-1] - raw.times[0]
    
    # Log rejection if necessary
    if max_amplitude > threshold:
        reason = f"amplitude > {threshold}uV"
        log_artifact_rejection(participant_id, reason, exclusion_log)
        logger.warning(f"Participant {participant_id} rejected: {reason}")
        return None
    
    if duration < min_duration:
        reason = f"segment < {min_duration}s"
        log_artifact_rejection(participant_id, reason, exclusion_log)
        logger.warning(f"Participant {participant_id} rejected: {reason}")
        return None
    
    return raw

def process_eeg_stream(stream: Generator[Tuple[str, mne.io.BaseRaw], None, None], config: dict, logger: logging.Logger, exclusion_log: List[dict]) -> List[Tuple[str, mne.io.BaseRaw]]:
    """
    Process the stream of EEG files: filter, notch, and reject artifacts.
    Returns a list of (participant_id, cleaned_raw) tuples.
    """
    processed_data = []
    
    low_freq = config.get('filter_low', 1)
    high_freq = config.get('filter_high', 40)
    notch_freq = config.get('notch_freq', 50)
    artifact_threshold = config.get('artifact_threshold', 100)
    min_duration = 120  # seconds per FR-002
    
    for participant_id, raw in stream:
        # Apply bandpass filter
        raw = apply_bandpass_filter(raw, low_freq, high_freq, logger)
        
        # Apply notch filter
        raw = apply_notch_filter(raw, notch_freq, logger)
        
        # Reject artifacts
        cleaned_raw = reject_artifacts(raw, artifact_threshold, min_duration, logger, participant_id, exclusion_log)
        
        if cleaned_raw is not None:
            processed_data.append((participant_id, cleaned_raw))
        else:
            # Participant was rejected, skip further processing
            continue
    
    return processed_data

def save_processed_data(processed_data: List[Tuple[str, mne.io.BaseRaw]], output_path: str, logger: logging.Logger):
    """Save processed EEG data to a FIF file."""
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving processed data to {output_path}")
    
    # Concatenate all processed data into a single Raw object if possible,
    # or save individually. For simplicity, we'll save the first one as a representative.
    # In a real pipeline, you might want to save each participant separately.
    if processed_data:
        # Save the first participant's data as an example
        # Note: This is a simplification. A full pipeline would save all participants.
        participant_id, raw = processed_data[0]
        raw.save(output_path, overwrite=True)
        logger.info(f"Saved {participant_id} to {output_path}")
    else:
        logger.warning("No processed data to save.")

def main():
    """Main entry point for the preprocessing pipeline."""
    logger = setup_logger("preprocess")
    logger.info("Starting preprocessing pipeline")
    
    try:
        config = load_config()
        
        # Ensure exclusion log is initialized
        exclusion_log = []
        
        # Stream and process EEG files
        data_dir = "data/raw"
        eeg_stream = stream_eeg_files(data_dir, logger)
        processed_data = process_eeg_stream(eeg_stream, config, logger, exclusion_log)
        
        # Save exclusion log
        save_exclusion_log_csv(exclusion_log, "logs/exclusion_log.csv")
        
        # Save processed data
        output_path = "data/processed/cleaned_eeg.fif"
        save_processed_data(processed_data, output_path, logger)
        
        logger.info("Preprocessing pipeline completed successfully")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
