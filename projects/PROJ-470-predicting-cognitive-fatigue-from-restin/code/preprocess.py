import os
import sys
import yaml
import numpy as np
import mne
from pathlib import Path
from typing import Generator, Tuple, Dict, Any, Optional
import logging

# Import from local utils
from utils.logging import get_logger, log_artifact_rejection, save_rejection_summary

def load_config(config_path: str = "code/config.yaml") -> Dict[str, Any]:
    """Load pipeline configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def stream_eeg_files(data_dir: str) -> Generator[Tuple[str, mne.io.Raw], None, None]:
    """
    Stream EEG files from the data directory one by one to minimize memory usage.
    Yields (filename, raw_object) tuples.
    
    This function implements the streaming pattern required for DC-001:
    Peak memory usage < 6GB by processing files sequentially and yielding
    control after each file is loaded.
    """
    data_path = Path(data_dir)
    if not data_path.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")
    
    # Supported extensions for EEG data
    extensions = ['.edf', '.bdf', '.vhdr', '.set', '.fif']
    
    for ext in extensions:
        for file_path in data_path.rglob(f"*{ext}"):
            try:
                # Load file in a streaming-friendly way
                # MNE-Python loads files into memory, but we process one at a time
                # and yield immediately to allow garbage collection
                raw = mne.io.read_raw_edf(str(file_path), preload=False) if ext == '.edf' else \
                      mne.io.read_raw_bdf(str(file_path), preload=False) if ext == '.bdf' else \
                      mne.io.read_raw_eeglab(str(file_path), preload=False) if ext == '.set' else \
                      mne.io.read_raw_fif(str(file_path), preload=False) if ext == '.fif' else \
                      mne.io.read_raw_brainvision(str(file_path), preload=False) if ext == '.vhdr' else None
                
                if raw is not None:
                    # Explicitly set preload=False to ensure streaming behavior
                    raw = raw.set_preload(False)
                    yield str(file_path.name), raw
            except Exception as e:
                logging.warning(f"Failed to load {file_path}: {e}")
                continue

def apply_bandpass_filter(
    raw: mne.io.Raw, 
    low_freq: float = 1.0, 
    high_freq: float = 40.0,
    logger: Optional[logging.Logger] = None
) -> mne.io.Raw:
    """
    Apply a 1-40 Hz bandpass filter to remove slow drifts and high-frequency noise.
    
    Implements FR-002: Bandpass filter 1-40 Hz.
    
    Args:
        raw: Raw EEG data object
        low_freq: Lower cutoff frequency (Hz)
        high_freq: Upper cutoff frequency (Hz)
        logger: Logger instance for progress tracking
        
    Returns:
        Filtered raw object (new instance, original unchanged)
    """
    if logger:
        logger.info(f"Applying bandpass filter: {low_freq}-{high_freq} Hz")
    
    # Create a copy to avoid modifying the original
    raw_filtered = raw.copy()
    
    # Apply filter with default settings (FIR, Hamming window)
    raw_filtered.filter(
        l_freq=low_freq,
        h_freq=high_freq,
        method='fir',
        fir_window='hamming',
        verbose=False
    )
    
    return raw_filtered

def reject_artifacts(
    raw: mne.io.Raw,
    threshold_microvolts: float = 100.0,
    min_duration_seconds: float = 120.0,
    logger: Optional[logging.Logger] = None
) -> Tuple[bool, str]:
    """
    Reject epochs based on amplitude threshold and minimum duration.
    
    Implements FR-002 and Edge Cases:
    - Exclude epochs >±100µV
    - Exclude segments <120 seconds
    
    Args:
        raw: Raw EEG data object
        threshold_microvolts: Maximum allowed amplitude (µV)
        min_duration_seconds: Minimum segment duration (seconds)
        logger: Logger instance for logging rejections
        
    Returns:
        Tuple of (is_valid, rejection_reason)
        is_valid: True if data passes all checks
        rejection_reason: Description of why data was rejected (empty if valid)
    """
    # Check minimum duration
    duration = raw.times[-1] - raw.times[0]
    if duration < min_duration_seconds:
        reason = f"Duration {duration:.1f}s < {min_duration_seconds}s minimum"
        if logger:
            log_artifact_rejection(logger, reason, duration=duration)
        return False, reason
    
    # Check amplitude threshold
    data = raw.get_data()
    max_amplitude = np.max(np.abs(data))
    if max_amplitude > threshold_microvolts:
        reason = f"Max amplitude {max_amplitude:.1f}µV > {threshold_microvolts}µV threshold"
        if logger:
            log_artifact_rejection(logger, reason, max_amplitude=max_amplitude)
        return False, reason
    
    return True, ""

def process_eeg_stream(
    stream: Generator[Tuple[str, mne.io.Raw], None, None],
    config: Dict[str, Any],
    logger: logging.Logger
) -> Tuple[Dict[str, np.ndarray], Dict[str, Any]]:
    """
    Process EEG data stream with filtering and artifact rejection.
    
    Implements streaming processing to ensure peak memory < 6GB (DC-001).
    Processes each file individually, applies filters, rejects artifacts,
    and accumulates valid data in a dictionary structure.
    
    Args:
        stream: Generator yielding (filename, raw) tuples
        config: Configuration dictionary with filter and rejection parameters
        logger: Logger instance for tracking progress
        
    Returns:
        Tuple of (processed_data_dict, summary_stats)
        processed_data_dict: Dict mapping participant IDs to processed numpy arrays
        summary_stats: Dict with rejection counts and processing statistics
    """
    processed_data = {}
    summary = {
        'total_files': 0,
        'accepted_files': 0,
        'rejected_files': 0,
        'rejection_reasons': {},
        'processing_time_per_file': []
    }
    
    # Get parameters from config
    filter_config = config.get('filter', {})
    low_freq = filter_config.get('low_freq', 1.0)
    high_freq = filter_config.get('high_freq', 40.0)
    
    artifact_config = config.get('artifact_rejection', {})
    threshold = artifact_config.get('threshold_microvolts', 100.0)
    min_duration = artifact_config.get('min_duration_seconds', 120.0)
    
    for filename, raw in stream:
        summary['total_files'] += 1
        start_time = time.time()
        
        try:
            # Apply bandpass filter
            raw_filtered = apply_bandpass_filter(raw, low_freq, high_freq, logger)
            
            # Check for artifacts
            is_valid, reason = reject_artifacts(raw_filtered, threshold, min_duration, logger)
            
            if is_valid:
                # Extract data and metadata
                data = raw_filtered.get_data()
                participant_id = filename.split('_')[0] if '_' in filename else f"participant_{summary['accepted_files']}"
                
                processed_data[participant_id] = data
                summary['accepted_files'] += 1
                logger.info(f"Accepted {filename}: shape={data.shape}, duration={raw_filtered.times[-1]:.1f}s")
            else:
                summary['rejected_files'] += 1
                summary['rejection_reasons'][reason] = summary['rejection_reasons'].get(reason, 0) + 1
                logger.warning(f"Rejected {filename}: {reason}")
                
        except Exception as e:
            summary['rejected_files'] += 1
            error_reason = f"Processing error: {str(e)}"
            summary['rejection_reasons'][error_reason] = summary['rejection_reasons'].get(error_reason, 0) + 1
            logger.error(f"Error processing {filename}: {e}")
        
        end_time = time.time()
        summary['processing_time_per_file'].append(end_time - start_time)
        
        # Explicit garbage collection to ensure memory stays under 6GB
        import gc
        gc.collect()
    
    # Calculate summary statistics
    if summary['processing_time_per_file']:
        summary['avg_processing_time'] = np.mean(summary['processing_time_per_file'])
        summary['max_processing_time'] = np.max(summary['processing_time_per_file'])
    del summary['processing_time_per_file']
    
    return processed_data, summary

def save_processed_data(
    processed_data: Dict[str, np.ndarray],
    output_path: str,
    logger: logging.Logger
) -> None:
    """
    Save processed EEG data to disk in a memory-efficient format.
    
    Args:
        processed_data: Dictionary mapping participant IDs to numpy arrays
        output_path: Path for output file (supports .npy or .npz)
        logger: Logger instance for progress tracking
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if output_path.suffix == '.npy':
        # Save single array if only one participant
        if len(processed_data) == 1:
            data = list(processed_data.values())[0]
            np.save(output_path, data)
            logger.info(f"Saved processed data to {output_path} (shape: {data.shape})")
        else:
            # For multiple participants, save as .npz
            np.savez_compressed(output_path.with_suffix('.npz'), **processed_data)
            logger.info(f"Saved processed data to {output_path.with_suffix('.npz')} ({len(processed_data)} participants)")
    elif output_path.suffix == '.npz':
        np.savez_compressed(output_path, **processed_data)
        logger.info(f"Saved processed data to {output_path} ({len(processed_data)} participants)")
    else:
        # Default to .npz for multiple participants
        np.savez_compressed(output_path.with_suffix('.npz'), **processed_data)
        logger.info(f"Saved processed data to {output_path.with_suffix('.npz')} ({len(processed_data)} participants)")

def main():
    """Main entry point for the preprocessing pipeline."""
    import time
    
    # Setup logging
    logger = get_logger('preprocess')
    logger.info("Starting preprocessing pipeline")
    
    # Load configuration
    try:
        config = load_config()
    except FileNotFoundError:
        logger.error("Configuration file not found. Using defaults.")
        config = {
            'filter': {'low_freq': 1.0, 'high_freq': 40.0},
            'artifact_rejection': {'threshold_microvolts': 100.0, 'min_duration_seconds': 120.0},
            'data': {'raw_dir': 'data/raw', 'processed_dir': 'data/processed'}
        }
    
    # Get directories from config
    raw_dir = config.get('data', {}).get('raw_dir', 'data/raw')
    processed_dir = config.get('data', {}).get('processed_dir', 'data/processed')
    output_file = config.get('data', {}).get('output_file', 'preprocessed_eeg.npy')
    
    # Validate data directory exists
    if not os.path.exists(raw_dir):
        logger.error(f"Data directory not found: {raw_dir}")
        # Create empty output to prevent cascade failures
        Path(processed_dir).mkdir(parents=True, exist_ok=True)
        np.save(os.path.join(processed_dir, output_file), np.array([]))
        sys.exit(1)
    
    # Create output directory
    Path(processed_dir).mkdir(parents=True, exist_ok=True)
    
    # Stream and process EEG files
    logger.info(f"Streaming EEG files from: {raw_dir}")
    stream = stream_eeg_files(raw_dir)
    
    processed_data, summary = process_eeg_stream(stream, config, logger)
    
    # Save results
    output_path = os.path.join(processed_dir, output_file)
    save_processed_data(processed_data, output_path, logger)
    
    # Log summary
    logger.info(f"Processing complete. Summary: {summary}")
    
    # Save rejection summary
    save_rejection_summary(summary, os.path.join(processed_dir, 'rejection_summary.json'))
    
    # Exit with appropriate code
    if summary['rejected_files'] == summary['total_files'] and summary['total_files'] > 0:
        logger.error("All files were rejected. Check data quality.")
        sys.exit(1)
    
    logger.info("Preprocessing pipeline completed successfully")

if __name__ == "__main__":
    main()