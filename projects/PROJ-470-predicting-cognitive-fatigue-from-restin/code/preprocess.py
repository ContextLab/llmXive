"""
Preprocessing pipeline for EEG data.
Applies bandpass filtering and artifact rejection.
"""
import os
import sys
import yaml
import numpy as np
import mne
from pathlib import Path
from utils.logging import get_logger, log_artifact_rejection, save_rejection_summary

def load_config(config_path='code/config.yaml'):
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def stream_eeg_files(data_dir):
    """
    Generator that yields EEG raw objects from the data directory.
    Handles streaming to keep memory usage low.
    """
    data_path = Path(data_dir)
    # Support .edf and .bdf extensions commonly used in PhysioNet datasets
    eeg_files = list(data_path.glob('*.edf')) + list(data_path.glob('*.bdf'))
    
    for file_path in eeg_files:
        try:
            raw = mne.io.read_raw_edf(file_path, preload=False, verbose=False)
            yield file_path.name, raw
        except Exception as e:
            logger = get_logger()
            logger.warning(f"Failed to load {file_path}: {e}")
            continue

def apply_bandpass_filter(raw, config):
    """
    Apply 1-40 Hz bandpass filter using MNE-Python.
    Per FR-002.
    """
    l_freq = config.get('filter', {}).get('low_cutoff', 1.0)
    h_freq = config.get('filter', {}).get('high_cutoff', 40.0)
    
    # Apply filter in-place to avoid copying data unnecessarily
    raw.filter(l_freq=l_freq, h_freq=h_freq, method='fir', n_jobs=1)
    
    return raw

def reject_artifacts(raw, config, logger):
    """
    Reject epochs/segments based on amplitude thresholds and duration.
    - Exclude epochs > ±100µV
    - Exclude segments < 120 seconds
    
    Returns:
        tuple: (cleaned_raw or None, accepted_count, rejected_count)
    """
    threshold = config.get('artifact', {}).get('threshold_uv', 100.0)
    min_duration = config.get('artifact', {}).get('min_duration_sec', 120.0)
    
    # Get subject ID for logging
    subject_id = 'unknown'
    if raw.info.get('subject_info') and raw.info['subject_info'].get('subject_id'):
        subject_id = raw.info['subject_info']['subject_id']
    
    # Check segment duration first
    duration = raw.times[-1] - raw.times[0]
    if duration < min_duration:
        log_artifact_rejection(logger, subject_id, 
                               'segment_too_short', 
                               f"Duration {duration:.2f}s < {min_duration}s")
        return None, 0, 1

    # Convert to microvolts for threshold check (MNE usually stores in Volts)
    data = raw.get_data() * 1e6 
    max_amplitude = np.max(np.abs(data))
    
    if max_amplitude > threshold:
        log_artifact_rejection(logger, subject_id,
                               'amplitude_exceeded', 
                               f"Max amplitude {max_amplitude:.2f}µV > {threshold}µV")
        return None, 0, 1

    return raw, 1, 0

def process_eeg_stream(data_dir, output_dir, config):
    """
    Process the stream of EEG files: filter and reject artifacts.
    Writes cleaned data to output directory.
    Logs exclusion counts and reasons as required by T011.
    """
    logger = get_logger()
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    total_processed = 0
    total_rejected = 0
    rejection_counts = {'amplitude_exceeded': 0, 'segment_too_short': 0}
    
    for filename, raw in stream_eeg_files(data_dir):
        subject_id = raw.info['subject_info']['subject_id'] if raw.info['subject_info'] else filename.replace('.edf', '').replace('.bdf', '')
        
        # Apply Bandpass Filter
        try:
            raw_filtered = apply_bandpass_filter(raw, config)
        except Exception as e:
            logger.error(f"Filtering failed for {filename}: {e}")
            continue
        
        # Apply Artifact Rejection (T011 implementation)
        raw_clean, accepted, rejected = reject_artifacts(raw_filtered, config, logger)
        
        if raw_clean is None:
            total_rejected += 1
            if rejected > 0:
                # Determine reason from the rejection log context or re-check logic
                # Since reject_artifacts returns 1 in rejected slot if amplitude, else 0 (duration)
                # We need to be careful: the function returns (None, 0, 1) for both cases
                # We'll rely on the log message or a slight adjustment in logic if needed.
                # However, the log_artifact_rejection call inside reject_artifacts already logged the reason.
                # We just need to count correctly here.
                # Let's refine the return logic in reject_artifacts to be clearer or infer here.
                # For now, we assume the order of checks: duration first, then amplitude.
                # If it failed duration, rejected=1, amplitude=0.
                # If it failed amplitude, rejected=1, duration=0.
                # We can't distinguish purely by the return value (0,1) vs (0,1) without internal state.
                # We will trust the log file for the specific reason breakdown, 
                # but for the summary counts, we need to track which reason occurred.
                # Re-implementing the check here for accurate counting in the summary:
                duration = raw_filtered.times[-1] - raw_filtered.times[0]
                data = raw_filtered.get_data() * 1e6
                max_amp = np.max(np.abs(data))
                
                if duration < config.get('artifact', {}).get('min_duration_sec', 120.0):
                    rejection_counts['segment_too_short'] += 1
                else:
                    rejection_counts['amplitude_exceeded'] += 1
            continue
        
        # Save cleaned data
        output_file = output_path / f"cleaned_{subject_id}.edf"
        raw_clean.save(output_file, overwrite=True)
        total_processed += 1
        
        logger.info(f"Processed and saved: {output_file}")
    
    # Save rejection summary
    summary = {
        'total_processed': total_processed,
        'total_rejected': total_rejected,
        'rejection_counts': rejection_counts
    }
    save_rejection_summary(logger, summary)
    logger.info(f"Rejection Summary: {rejection_counts}")
    return summary

def main():
    """Main entry point for preprocessing."""
    config = load_config()
    data_dir = config.get('paths', {}).get('raw_data', 'data/raw')
    output_dir = config.get('paths', {}).get('processed_data', 'data/processed')
    
    logger = get_logger()
    logger.info("Starting preprocessing pipeline...")
    
    results = process_eeg_stream(data_dir, output_dir, config)
    
    logger.info(f"Preprocessing complete. Processed: {results['total_processed']}, Rejected: {results['total_rejected']}")
    logger.info(f"Rejection details: {results['rejection_counts']}")

if __name__ == '__main__':
    main()