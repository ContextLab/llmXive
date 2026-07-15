import os
import sys
import yaml
import numpy as np
import mne
from pathlib import Path
import logging
from datetime import datetime

# Import from local utils
from utils.logging import get_logger, log_artifact_rejection, save_rejection_summary, get_rejection_counts

def load_config(config_path="code/config.yaml"):
    """Load pipeline configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def stream_eeg_files(data_dir, file_pattern="*.edf"):
    """
    Stream EEG files from a directory.
    Yields (filename, raw_object) tuples.
    """
    data_path = Path(data_dir)
    if not data_path.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")
    
    files = list(data_path.glob(file_pattern))
    if not files:
        # Also try .bdf or .vhdr if no edf found
        files = list(data_path.glob("*.bdf")) + list(data_path.glob("*.vhdr"))
    
    logger = get_logger("preprocess")
    logger.info(f"Found {len(files)} potential EEG files in {data_dir}")
    
    for file_path in files:
        try:
            # MNE can handle various formats automatically
            raw = mne.io.read_raw_edf(file_path, preload=False, verbose=False)
            yield str(file_path.name), raw
        except Exception as e:
            logger.warning(f"Could not read {file_path}: {e}")
            continue

def apply_bandpass_filter(raw, l_freq=1.0, h_freq=40.0, logger=None):
    """
    Apply bandpass filter (1-40 Hz) to raw data.
    Returns filtered raw object.
    """
    if logger is None:
        logger = get_logger("preprocess")
    
    logger.info(f"Applying bandpass filter: {l_freq}-{h_freq} Hz")
    
    # Set montage if not present (standard 10-20)
    if raw.get_montage() is None:
        try:
            raw.set_montage('standard_1005', match_case=False, match_alias=True, on_missing='ignore')
        except Exception:
            pass # Ignore if montage cannot be set
    
    # Filter
    raw_filtered = raw.copy()
    raw_filtered.filter(l_freq=l_freq, h_freq=h_freq, method='fir', fir_window='hamming', n_jobs=1)
    
    return raw_filtered

def reject_artifacts(raw, amplitude_threshold=100.0, min_segment_duration=120.0, logger=None):
    """
    Reject artifacts from EEG data based on amplitude and segment duration.
    
    Parameters:
    -----------
    raw : mne.io.Raw
        Raw EEG data object (should be filtered first).
    amplitude_threshold : float
        Threshold in microvolts (µV) for amplitude rejection. Default ±100µV.
    min_segment_duration : float
        Minimum segment duration in seconds. Default 120s.
    logger : logging.Logger
        Logger instance.
    
    Returns:
    --------
    mne.io.Raw
        Raw data with bad segments marked.
    dict
        Summary of rejected segments.
    """
    if logger is None:
        logger = get_logger("preprocess")
    
    logger.info(f"Starting artifact rejection: threshold={amplitude_threshold}µV, min_duration={min_segment_duration}s")
    
    # Convert to microvolts if necessary (MNE usually uses Volts)
    # Check data unit
    info = raw.info
    ch_names = raw.ch_names
    
    # Extract data and channel units
    data = raw.get_data()
    # MNE stores data in Volts, so convert threshold to Volts
    threshold_volts = amplitude_threshold * 1e-6
    
    # Find bad segments based on amplitude
    # We iterate through channels and find segments exceeding threshold
    bad_segments = []
    channel_rejections = {}
    
    # Estimate segment length (e.g., 2s windows) for analysis
    sfreq = raw.info['sfreq']
    window_size = int(2 * sfreq) # 2 second windows
    
    rejected_count = 0
    amplitude_rejections = 0
    duration_rejections = 0
    
    # Check each channel for amplitude violations
    for idx, ch_name in enumerate(ch_names):
        ch_data = data[idx, :]
        # Find indices where amplitude exceeds threshold
        exceeds = np.abs(ch_data) > threshold_volts
        
        # Group consecutive exceeds into segments
        if np.any(exceeds):
            # Simple approach: mark entire recording as bad if too many points exceed
            # Or find specific windows
            exceed_ratio = np.mean(exceeds)
            if exceed_ratio > 0.1: # If >10% of data is bad in this channel
                channel_rejections[ch_name] = exceed_ratio
                amplitude_rejections += 1
                logger.warning(f"Channel {ch_name}: {exceed_ratio:.2%} of data exceeds threshold")
    
    # Determine if the entire recording is too short
    duration = raw.times[-1]
    if duration < min_segment_duration:
        duration_rejections += 1
        logger.warning(f"Recording duration ({duration:.1f}s) is less than minimum ({min_segment_duration}s)")
        # Mark the whole recording as bad by creating a single bad segment
        bad_segments.append((0, int(duration * sfreq)))
    else:
        # Check for short segments within the recording if we want to be more granular
        # For now, we focus on the global duration and amplitude thresholds
        pass
    
    # Create annotation for bad segments
    # If we have specific bad windows, add them. Otherwise, if the whole thing is bad, add it.
    if bad_segments:
        # Convert indices to times
        bad_times = [(start / sfreq, end / sfreq) for start, end in bad_segments]
        descriptions = ['bad_segment'] * len(bad_times)
        annot = mne.Annotations(onset=[t[0] for t in bad_times],
                                duration=[t[1] - t[0] for t in bad_times],
                                description=descriptions)
        raw.set_annotations(annot)
    
    rejection_summary = {
        'total_channels': len(ch_names),
        'channels_rejected': amplitude_rejections,
        'duration_rejected': duration_rejections,
        'bad_segments': bad_segments,
        'channel_details': channel_rejections,
        'reason': 'amplitude' if amplitude_rejections > 0 else ('duration' if duration_rejections > 0 else 'none')
    }
    
    # Log the rejection details
    log_artifact_rejection(
        logger=logger,
        participant_id=raw.info.get('subject_info', {}).get('his_id', 'unknown'),
        reason=rejection_summary['reason'],
        count=amplitude_rejections + duration_rejections,
        details=rejection_summary
    )
    
    logger.info(f"Artifact rejection complete. Rejected {amplitude_rejections} channels (amplitude), {duration_rejections} segments (duration).")
    
    return raw, rejection_summary

def process_eeg_stream(stream, config, logger=None):
    """
    Process a stream of EEG files: filter and reject artifacts.
    
    Parameters:
    -----------
    stream : generator
        Generator yielding (filename, raw_object) tuples.
    config : dict
        Configuration dictionary.
    logger : logging.Logger
        Logger instance.
    
    Returns:
    --------
    list
        List of processed raw objects.
    dict
        Aggregated rejection summary.
    """
    if logger is None:
        logger = get_logger("preprocess")
    
    processed_data = []
    aggregated_summary = {
        'processed_count': 0,
        'rejected_count': 0,
        'total_rejections': [],
        'details': []
    }
    
    l_freq = config.get('filter', {}).get('l_freq', 1.0)
    h_freq = config.get('filter', {}).get('h_freq', 40.0)
    amplitude_threshold = config.get('artifact', {}).get('amplitude_threshold', 100.0)
    min_duration = config.get('artifact', {}).get('min_segment_duration', 120.0)
    
    for filename, raw in stream:
        logger.info(f"Processing {filename}")
        
        # Apply bandpass filter
        try:
            raw_filtered = apply_bandpass_filter(raw, l_freq, h_freq, logger)
        except Exception as e:
            logger.error(f"Failed to filter {filename}: {e}")
            aggregated_summary['rejected_count'] += 1
            aggregated_summary['total_rejections'].append({'file': filename, 'reason': 'filter_error', 'error': str(e)})
            continue
        
        # Apply artifact rejection
        try:
            raw_clean, rejection_info = reject_artifacts(
                raw_filtered, 
                amplitude_threshold, 
                min_duration, 
                logger
            )
            
            # Check if the recording is still valid after rejection
            # If the whole recording was rejected (e.g. too short), skip it
            if rejection_info['duration_rejected'] > 0:
                logger.warning(f"Skipping {filename} due to duration rejection")
                aggregated_summary['rejected_count'] += 1
                aggregated_summary['total_rejections'].append({'file': filename, 'reason': 'duration'})
                continue
            
            # If too many channels were rejected, consider the whole recording bad
            if rejection_info['channels_rejected'] > (len(raw.info['ch_names']) * 0.5):
                logger.warning(f"Skipping {filename} due to excessive channel rejection")
                aggregated_summary['rejected_count'] += 1
                aggregated_summary['total_rejections'].append({'file': filename, 'reason': 'excessive_artifacts'})
                continue
            
            processed_data.append(raw_clean)
            aggregated_summary['processed_count'] += 1
            aggregated_summary['details'].append({
                'file': filename,
                'status': 'processed',
                'rejection_info': rejection_info
            })
            
        except Exception as e:
            logger.error(f"Failed to reject artifacts for {filename}: {e}")
            aggregated_summary['rejected_count'] += 1
            aggregated_summary['total_rejections'].append({'file': filename, 'reason': 'artifact_error', 'error': str(e)})
            continue
    
    return processed_data, aggregated_summary

def main():
    """Main entry point for preprocessing pipeline."""
    config = load_config()
    logger = get_logger("preprocess")
    
    logger.info("Starting preprocessing pipeline")
    
    data_dir = config.get('data', {}).get('raw_dir', 'data/raw')
    output_dir = config.get('data', {}).get('processed_dir', 'data/processed')
    
    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Stream and process files
    stream = stream_eeg_files(data_dir)
    processed_data, summary = process_eeg_stream(stream, config, logger)
    
    # Save processed data
    if processed_data:
        # Save each file individually or concatenate
        # For now, save the first valid one as a representative sample
        # In a real pipeline, we might save all or concatenate
        sample_raw = processed_data[0]
        output_path = Path(output_dir) / "preprocessed_eeg_raw.fif"
        logger.info(f"Saving processed data to {output_path}")
        sample_raw.save(output_path, overwrite=True)
        
        # Save rejection summary
        summary_path = Path(output_dir) / "rejection_summary.json"
        with open(summary_path, 'w') as f:
            import json
            json.dump(summary, f, indent=2, default=str)
        logger.info(f"Saved rejection summary to {summary_path}")
        
        logger.info(f"Successfully processed {summary['processed_count']} files, rejected {summary['rejected_count']}")
    else:
        logger.error("No valid data found after preprocessing")
        # Write a failure report
        report_path = Path(output_dir) / "preprocessing_failed.json"
        with open(report_path, 'w') as f:
            json.dump({'status': 'failed', 'reason': 'No valid data', 'summary': summary}, f)
        sys.exit(1)

if __name__ == "__main__":
    main()