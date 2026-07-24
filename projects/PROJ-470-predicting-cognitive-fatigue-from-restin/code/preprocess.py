import os
import sys
import yaml
import logging
import numpy as np
import mne
from pathlib import Path
from datetime import datetime
from typing import Generator, Tuple, Optional, List, Dict, Any

# Import logging utilities from the shared utils module
from utils.logging import log_artifact_rejection, save_exclusion_log_csv

def load_config(config_path: str = "code/config.yaml") -> Dict[str, Any]:
    """Load pipeline configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def setup_logger(log_file: str = "logs/pipeline.log") -> logging.Logger:
    """Set up the logger ensuring the directory exists."""
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    logger = logging.getLogger("preprocess_pipeline")
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers to avoid duplicates
    if logger.handlers:
        logger.handlers.clear()
    
    file_handler = logging.FileHandler(log_file, mode='a')
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

def stream_eeg_files(raw_dir: str, extension: str = ".fif") -> Generator[Tuple[str, mne.io.Raw], None, None]:
    """
    Generator that yields (participant_id, raw_eeg_object) tuples.
    Uses preload=False to ensure memory efficiency (DC-001).
    """
    raw_path = Path(raw_dir)
    if not raw_path.exists():
        raise FileNotFoundError(f"Data directory not found: {raw_dir}")
    
    for file_path in raw_path.glob(f"*{extension}"):
        try:
            # CRITICAL: preload=False for streaming/memory safety
            raw = mne.io.read_raw_fif(file_path, preload=False)
            # Extract participant_id from filename (e.g., 'sub-001_eeg.fif' -> '001')
            participant_id = file_path.stem.split('_')[0].replace('sub-', '')
            yield participant_id, raw
        except Exception as e:
            logging.warning(f"Failed to load {file_path}: {e}")
            continue

def apply_bandpass_filter(raw: mne.io.Raw, low_freq: float = 1.0, high_freq: float = 40.0) -> mne.io.Raw:
    """Apply bandpass filter (1-40 Hz) to the raw data."""
    # Filter in place
    raw.filter(low_freq, high_freq, method='fir', fir_design='firwin')
    return raw

def detect_line_noise_peak(raw: mne.io.Raw) -> float:
    """Detect the peak frequency in the 45-55 Hz range to identify line noise."""
    # Compute PSD
    psd, freqs = mne.time_frequency.psd_welch(raw, fmin=45, fmax=55, n_fft=256)
    mean_psd = psd.mean(axis=0)
    peak_idx = np.argmax(mean_psd)
    return freqs[peak_idx]

def apply_notch_filter(raw: mne.io.Raw, notch_freq: float = 50.0) -> mne.io.Raw:
    """Apply notch filter to remove line noise."""
    raw.notch_filter(notch_freq, method='spectrum_fit')
    return raw

def reject_artifacts(raw: mne.io.Raw, amplitude_threshold: float = 100.0, min_duration: float = 120.0, logger: Optional[logging.Logger] = None) -> Tuple[bool, str, Optional[List[str]]]:
    """
    Reject artifacts based on amplitude and duration.
    
    Returns:
      Tuple[is_valid, reason, rejected_channels]
      - is_valid: True if data passes all checks
      - reason: Description of rejection if invalid, or "passed"
      - rejected_channels: List of channels rejected for amplitude (if any)
    """
    # 1. Check Duration
    duration = raw.times[-1] - raw.times[0]
    if duration < min_duration:
        return False, f"segment < {int(min_duration)}s", None

    # 2. Check Amplitude (Peak-to-Peak)
    # Get data (channels x time)
    data = raw.get_data()
    ptp = np.ptp(data, axis=1) # Peak-to-peak per channel
    
    # Convert threshold to Volts (MNE uses Volts internally)
    threshold_volts = amplitude_threshold * 1e-6
    
    bad_channels = []
    for i, ch_name in enumerate(raw.ch_names):
        if ptp[i] > threshold_volts:
            bad_channels.append(ch_name)
    
    if bad_channels:
        reason = f"amplitude > {int(amplitude_threshold)}uV"
        return False, reason, bad_channels

    return True, "passed", None

def process_eeg_stream(raw_dir: str, config: Dict[str, Any], logger: logging.Logger) -> None:
    """
    Process the stream of EEG files: Filter, Notch, Reject Artifacts.
    Writes exclusion log to logs/exclusion_log.csv.
    """
    low_freq = config.get('filter_low', 1.0)
    high_freq = config.get('filter_high', 40.0)
    notch_freq = config.get('notch_frequency', 50.0)
    artifact_threshold = config.get('artifact_threshold', 100.0)
    min_duration = config.get('min_duration', 120.0)
    
    processed_dir = Path("data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    exclusion_log_path = Path("logs/exclusion_log.csv")
    exclusion_log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Prepare exclusion log data
    exclusion_records = []
    
    for participant_id, raw in stream_eeg_files(raw_dir):
        logger.info(f"Processing participant: {participant_id}")
        
        try:
            # 1. Apply Bandpass
            raw = apply_bandpass_filter(raw, low_freq, high_freq)
            
            # 2. Apply Notch
            raw = apply_notch_filter(raw, notch_freq)
            
            # 3. Reject Artifacts
            is_valid, reason, bad_channels = reject_artifacts(
                raw, 
                amplitude_threshold=artifact_threshold, 
                min_duration=min_duration,
                logger=logger
            )
            
            if not is_valid:
                logger.warning(f"Participant {participant_id} rejected: {reason}")
                exclusion_records.append({
                    "participant_id": participant_id,
                    "reason": reason,
                    "timestamp": datetime.now().isoformat()
                })
                # Log to the shared exclusion log utility
                log_artifact_rejection(participant_id, reason, exclusion_log_path)
                continue
            
            # 4. Save Valid Data
            # Save as FIF for downstream compatibility
            output_path = processed_dir / f"cleaned_eeg_{participant_id}.fif"
            raw.save(output_path, overwrite=True)
            logger.info(f"Saved cleaned data for {participant_id} to {output_path}")
            
        except Exception as e:
            logger.error(f"Critical error processing {participant_id}: {e}")
            exclusion_records.append({
                "participant_id": participant_id,
                "reason": f"processing_error: {str(e)}",
                "timestamp": datetime.now().isoformat()
            })
            log_artifact_rejection(participant_id, f"processing_error: {str(e)}", exclusion_log_path)

def save_processed_data(processed_dir: str = "data/processed") -> None:
    """Placeholder for final aggregation if needed, currently handled in stream."""
    pass

def main():
    """Main entry point for the preprocessing pipeline."""
    logger = setup_logger()
    logger.info("Starting preprocessing pipeline")
    
    try:
        config = load_config()
        raw_dir = config.get('raw_data_dir', 'data/raw')
        
        if not os.path.exists(raw_dir):
            logger.error(f"Data directory not found: {raw_dir}")
            sys.exit(1)
        
        process_eeg_stream(raw_dir, config, logger)
        logger.info("Preprocessing pipeline completed successfully")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
