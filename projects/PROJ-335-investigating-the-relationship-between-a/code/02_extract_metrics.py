"""
User Story 2: Extract Alpha Power and PLV Metrics

This script computes alpha-band power from frontal/parietal electrodes
and pairwise phase-locking values (PLV) between frontal-parietal sites
during delay periods.

It includes strict validation to ensure required electrodes are present
before processing.
"""
import os
import sys
import json
import logging
import glob
from pathlib import Path

import numpy as np
from scipy.signal import hilbert, butter, filtfilt

# Import project utilities and models
from utils.validation import exit_on_validation_failure, log_error
from utils.logging_config import setup_logging, get_logger
from models.alpha_power import AlphaPowerMetric, AlphaPowerCollection
from models.plv_metric import PLVMetric, PLVCollection

# Configure logging
logger = get_logger(__name__)

def load_config():
    """Load configuration from code/config.yaml."""
    config_path = Path("code/config.yaml")
    if not config_path.exists():
        logger.error(f"Configuration file not found: {config_path}")
        sys.exit(1)
    
    import yaml
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def load_epochs_from_npz(subject_id, data_dir):
    """
    Load preprocessed epochs for a specific subject from NPZ file.
    
    Args:
        subject_id: Subject identifier (e.g., 'sub-01')
        data_dir: Path to data/processed directory
        
    Returns:
        dict containing epochs data
    """
    file_pattern = os.path.join(data_dir, f"{subject_id}_*.npz")
    files = glob.glob(file_pattern)
    
    if not files:
        logger.warning(f"No epochs file found for subject {subject_id}")
        return None
    
    # Load the first matching file
    data = np.load(files[0], allow_pickle=True)
    return data

def bandpass_filter(data, sfreq, lowcut=1.0, highcut=40.0, order=4):
    """Apply bandpass filter to EEG data."""
    nyquist = 0.5 * sfreq
    low = lowcut / nyquist
    high = highcut / nyquist
    
    b, a = butter(order, [low, high], btype='band')
    filtered_data = filtfilt(b, a, data, axis=-1)
    return filtered_data

def extract_alpha_power(epochs_data, channel_indices, sfreq):
    """
    Extract alpha band power (8-13 Hz) from specified channels.
    
    Args:
        epochs_data: Preprocessed epochs data
        channel_indices: Indices of channels to extract power from
        sfreq: Sampling frequency
        
    Returns:
        dict mapping channel names to average alpha power
    """
    # Filter for alpha band
    alpha_low, alpha_high = 8.0, 13.0
    alpha_filtered = bandpass_filter(
        epochs_data['data'], sfreq, alpha_low, alpha_high
    )
    
    # Calculate power (square of amplitude)
    power = np.mean(alpha_filtered ** 2, axis=(0, 2))  # Average over time and trials
    
    return power

def calculate_plv(epochs_data, channel_indices_1, channel_indices_2, sfreq):
    """
    Calculate Phase Locking Value (PLV) between two sets of channels.
    
    Args:
        epochs_data: Preprocessed epochs data
        channel_indices_1: Indices of first set of channels (e.g., frontal)
        channel_indices_2: Indices of second set of channels (e.g., parietal)
        sfreq: Sampling frequency
        
    Returns:
        PLV value between the channel sets
    """
    # Filter for alpha band
    alpha_low, alpha_high = 8.0, 13.0
    alpha_filtered = bandpass_filter(
        epochs_data['data'], sfreq, alpha_low, alpha_high
    )
    
    # Apply Hilbert transform to get instantaneous phase
    analytic_signal_1 = hilbert(alpha_filtered[:, channel_indices_1, :], axis=2)
    analytic_signal_2 = hilbert(alpha_filtered[:, channel_indices_2, :], axis=2)
    
    phase_1 = np.angle(analytic_signal_1)
    phase_2 = np.angle(analytic_signal_2)
    
    # Calculate phase difference
    phase_diff = phase_1 - phase_2
    
    # Calculate PLV (mean of complex exponentials of phase differences)
    plv = np.abs(np.mean(np.exp(1j * phase_diff), axis=(0, 2)))
    
    return plv

def validate_electrodes(epochs_data, required_electrodes):
    """
    Validate that all required electrodes are present in the data.
    
    Args:
        epochs_data: Dictionary containing channel names and data
        required_electrodes: List of required electrode names
        
    Returns:
        True if all electrodes are present, False otherwise
    """
    if 'channel_names' not in epochs_data:
        logger.error("CRITICAL: Missing channel names in epochs data")
        return False
    
    available_channels = list(epochs_data['channel_names'])
    missing_channels = []
    
    for electrode in required_electrodes:
        if electrode not in available_channels:
            missing_channels.append(electrode)
    
    if missing_channels:
        error_msg = f"CRITICAL: Missing required electrode data: {', '.join(missing_channels)}"
        log_error(error_msg)
        exit_on_validation_failure(error_msg, exit_code=1)
        return False
    
    logger.info("All required electrodes are present")
    return True

def process_all_subjects(config):
    """
    Process all subjects in the dataset.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Tuple of (alpha_power_collection, plv_collection)
    """
    data_dir = Path(config['paths']['processed'])
    alpha_collection = AlphaPowerCollection()
    plv_collection = PLVCollection()
    
    # Define required electrodes
    required_electrodes = config.get('analysis', {}).get('required_electrodes', 
                                                       ['Fz', 'Pz', 'F3', 'F4', 'P3', 'P4'])
    
    # Define electrode groups for PLV
    frontal_electrodes = config.get('analysis', {}).get('frontal_electrodes', 
                                                        ['Fz', 'F3', 'F4'])
    parietal_electrodes = config.get('analysis', {}).get('parietal_electrodes', 
                                                         ['Pz', 'P3', 'P4'])
    
    # Get list of subjects
    subject_files = glob.glob(os.path.join(data_dir, "sub-*_*.npz"))
    subjects = list(set([os.path.basename(f).split('_')[0] for f in subject_files]))
    
    for subject_id in subjects:
        logger.info(f"Processing subject: {subject_id}")
        
        # Load epochs
        epochs_data = load_epochs_from_npz(subject_id, data_dir)
        if epochs_data is None:
            logger.warning(f"Skipping subject {subject_id}: No data found")
            continue
        
        # Validate electrodes
        if not validate_electrodes(epochs_data, required_electrodes):
            continue
        
        # Get channel indices
        channel_names = list(epochs_data['channel_names'])
        sfreq = epochs_data.get('sfreq', 500)  # Default to 500 Hz if not specified
        
        # Extract alpha power for each channel
        for electrode in required_electrodes:
            if electrode in channel_names:
                idx = channel_names.index(electrode)
                power = extract_alpha_power(epochs_data, [idx], sfreq)[0]
                
                metric = AlphaPowerMetric(
                    subject_id=subject_id,
                    electrode=electrode,
                    alpha_power=float(power),
                    sfreq=sfreq
                )
                alpha_collection.add(metric)
        
        # Calculate PLV for frontal-parietal pairs
        for front in frontal_electrodes:
            for parietal in parietal_electrodes:
                if front in channel_names and parietal in channel_names:
                    front_idx = channel_names.index(front)
                    parietal_idx = channel_names.index(parietal)
                    
                    plv = calculate_plv(
                        epochs_data, [front_idx], [parietal_idx], sfreq
                    )[0]
                    
                    metric = PLVMetric(
                        subject_id=subject_id,
                        electrode_front=front,
                        electrode_parietal=parietal,
                        plv=float(plv),
                        sfreq=sfreq
                    )
                    plv_collection.add(metric)
    
    return alpha_collection, plv_collection

def main():
    """Main entry point for metric extraction."""
    setup_logging()
    logger.info("Starting metric extraction pipeline")
    
    try:
        # Load configuration
        config = load_config()
        
        # Process all subjects
        alpha_collection, plv_collection = process_all_subjects(config)
        
        # Save results
        output_dir = Path(config['paths']['metrics'])
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save alpha power metrics
        alpha_file = output_dir / "alpha_power.csv"
        alpha_collection.to_csv(alpha_file)
        logger.info(f"Saved alpha power metrics to {alpha_file}")
        
        # Save PLV metrics
        plv_file = output_dir / "plv.csv"
        plv_collection.to_csv(plv_file)
        logger.info(f"Saved PLV metrics to {plv_file}")
        
        logger.info("Metric extraction completed successfully")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()