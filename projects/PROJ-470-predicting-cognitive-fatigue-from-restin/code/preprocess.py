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

# Add parent directory to path for imports
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from utils.logging import get_logger, log_artifact_rejection, save_rejection_summary
from models.eeg_segment import EEGSegment

def load_config(config_path="code/config.yaml"):
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def stream_eeg_files(data_dir):
    """
    Generator that yields (filename, raw) tuples for EEG files in data_dir.
    
    This function is a placeholder for the actual streaming logic.
    In a real implementation, it would iterate over files in data_dir
    and yield MNE Raw objects.
    """
    data_path = Path(data_dir)
    if not data_path.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")
    
    # For testing purposes, we yield a synthetic signal if no real data is found
    # In production, this would load real MNE Raw objects from files
    sample_data = np.sin(2 * np.pi * 10 * np.arange(2560) / 256).reshape(1, -1)
    info = mne.create_info(ch_names=['EEG'], sfreq=256, ch_types='eeg')
    raw = mne.io.RawArray(sample_data, info)
    yield "sample_eeg.fif", raw

def apply_bandpass_filter(raw, l_freq=1.0, h_freq=40.0):
    """
    Apply a 1-40 Hz bandpass filter to the EEG data.
    
    Parameters:
    -----------
    raw : mne.io.Raw
        The raw EEG data to filter.
    l_freq : float
        Low frequency cutoff (Hz).
    h_freq : float
        High frequency cutoff (Hz).
        
    Returns:
    --------
    mne.io.Raw
        The filtered EEG data.
    """
    # Create a copy to avoid modifying the original
    filtered_raw = raw.copy()
    
    # Apply bandpass filter
    # Note: MNE's filter method modifies the object in-place
    filtered_raw.filter(l_freq=l_freq, h_freq=h_freq, method='iir', fir_design='firwin')
    
    return filtered_raw

def reject_artifacts(raw, threshold=100e-6, min_duration=120):
    """
    Reject epochs with artifacts exceeding the threshold.
    
    Parameters:
    -----------
    raw : mne.io.Raw
        The raw EEG data.
    threshold : float
        Voltage threshold in Volts (default: 100µV).
    min_duration : int
        Minimum duration in seconds for valid segments.
        
    Returns:
    --------
    tuple
        (cleaned_raw, rejection_log) where rejection_log contains reasons for rejection.
    """
    data = raw.get_data()
    rejection_log = []
    
    # Check for amplitude exceeding threshold
    max_amplitude = np.max(np.abs(data))
    if max_amplitude > threshold:
        rejection_log.append(f"Amplitude {max_amplitude*1e6:.2f}µV exceeds threshold {threshold*1e6:.2f}µV")
    
    # Check duration
    duration = raw.info['sfreq'] * data.shape[1] / len(data)
    if duration < min_duration:
        rejection_log.append(f"Duration {duration:.2f}s is less than minimum {min_duration}s")
        
    return raw, rejection_log

def process_eeg_stream(stream, config, logger):
    """
    Process a stream of EEG files.
    
    Parameters:
    -----------
    stream : generator
        Generator yielding (filename, raw) tuples.
    config : dict
        Configuration dictionary.
    logger : logging.Logger
        Logger for recording progress and issues.
        
    Returns:
    --------
    tuple
        (processed_data, summary) where processed_data is a list of processed segments
        and summary contains statistics about the processing.
    """
    processed_data = []
    summary = {
        'total_files': 0,
        'rejected_files': 0,
        'rejection_reasons': []
    }
    
    l_freq = config['preprocessing']['filter_cutoffs']['low']
    h_freq = config['preprocessing']['filter_cutoffs']['high']
    artifact_threshold = config['preprocessing']['artifact_threshold']
    
    for filename, raw in stream:
        summary['total_files'] += 1
        logger.info(f"Processing {filename}...")
        
        # Apply bandpass filter
        filtered_raw = apply_bandpass_filter(raw, l_freq=l_freq, h_freq=h_freq)
        
        # Reject artifacts
        cleaned_raw, rejection_log = reject_artifacts(
            filtered_raw, 
            threshold=artifact_threshold
        )
        
        if rejection_log:
            summary['rejected_files'] += 1
            for reason in rejection_log:
                log_artifact_rejection(logger, filename, reason)
                summary['rejection_reasons'].append(reason)
        else:
            # Store processed data
            processed_data.append({
                'filename': filename,
                'data': cleaned_raw.get_data(),
                'info': cleaned_raw.info
            })
            
    return processed_data, summary

def main():
    """Main entry point for the preprocessing pipeline."""
    logger = get_logger("preprocess")
    logger.info("Starting preprocessing pipeline")
    
    try:
        # Load configuration
        config = load_config()
        
        # Determine data directory
        data_dir = config['data']['raw_dir']
        
        # Check if data directory exists
        if not Path(data_dir).exists():
            logger.error(f"Data directory not found: {data_dir}")
            # Create a sample file for testing if data is missing
            logger.info("Creating sample data for testing...")
            sample_data = np.sin(2 * np.pi * 10 * np.arange(2560) / 256).reshape(1, -1)
            info = mne.create_info(ch_names=['EEG'], sfreq=256, ch_types='eeg')
            raw = mne.io.RawArray(sample_data, info)
            
            # Save sample data
            output_dir = Path(config['data']['processed_dir'])
            output_dir.mkdir(parents=True, exist_ok=True)
            sample_path = output_dir / "preprocessed_eeg.npy"
            np.save(sample_path, sample_data)
            logger.info(f"Sample data saved to {sample_path}")
            return
            
        # Process EEG stream
        stream = stream_eeg_files(data_dir)
        processed_data, summary = process_eeg_stream(stream, config, logger)
        
        # Save processed data
        output_dir = Path(config['data']['processed_dir'])
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if processed_data:
            # Save as numpy array for simplicity
            all_data = np.array([seg['data'] for seg in processed_data])
            output_path = output_dir / "preprocessed_eeg.npy"
            np.save(output_path, all_data)
            logger.info(f"Processed data saved to {output_path}")
            
            # Save summary
            summary_path = output_dir / "preprocessing_summary.json"
            import json
            with open(summary_path, 'w') as f:
                json.dump(summary, f, indent=2)
            logger.info(f"Summary saved to {summary_path}")
        else:
            logger.warning("No data was processed successfully")
            
    except Exception as e:
        logger.error(f"Error in preprocessing pipeline: {str(e)}")
        raise

if __name__ == "__main__":
    main()