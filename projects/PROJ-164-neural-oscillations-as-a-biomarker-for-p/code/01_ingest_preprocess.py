import os
import sys
import logging
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
import mne
import numpy as np

# Import shared utilities
from utils.config import ensure_dirs, DATA_PROCESSED, DATA_RAW
from utils.logging_setup import get_logger

# Configure logger
logger = get_logger(__name__)

def load_raw_edf(file_path: str) -> mne.io.BaseRaw:
    """Load an EDF file using MNE-Python.
    
    Args:
        file_path: Path to the EDF file.
        
    Returns:
        MNE Raw object.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        Exception: If loading fails.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"EDF file not found: {file_path}")
    
    logger.info(f"Loading EDF file: {file_path}")
    raw = mne.io.read_raw_edf(file_path, preload=True, verbose=False)
    logger.info(f"Loaded {len(raw.ch_names)} channels, {raw.n_times} time points")
    return raw

def apply_common_average_reference(raw: mne.io.BaseRaw) -> mne.io.BaseRaw:
    """Apply Common Average Reference (CAR) to the raw data.
    
    Args:
        raw: MNE Raw object.
        
    Returns:
        MNE Raw object with CAR applied.
    """
    logger.info("Applying Common Average Reference")
    raw_car = raw.copy().set_eeg_reference('average', projection=False)
    return raw_car

def apply_bandpass_filter(raw: mne.io.BaseRaw, l_freq: float = 1.0, h_freq: float = 45.0) -> mne.io.BaseRaw:
    """Apply band-pass filter (1-45 Hz) to the raw data.
    
    Args:
        raw: MNE Raw object.
        l_freq: Low cutoff frequency.
        h_freq: High cutoff frequency.
        
    Returns:
        MNE Raw object with filtering applied.
    """
    logger.info(f"Applying band-pass filter: {l_freq}-{h_freq} Hz")
    raw_filt = raw.copy().filter(l_freq=l_freq, h_freq=h_freq, verbose=False)
    return raw_filt

def detect_bad_channels(raw: mne.io.BaseRaw, z_threshold: float = 5.0) -> List[str]:
    """Automatically detect bad channels based on z-score of channel variance.
    
    Args:
        raw: MNE Raw object.
        z_threshold: Z-score threshold for flagging bad channels.
        
    Returns:
        List of bad channel names.
    """
    logger.info(f"Detecting bad channels with z-score threshold: {z_threshold}")
    
    # Get data and channel names
    data = raw.get_data()
    ch_names = raw.ch_names
    sfreq = raw.info['sfreq']
    
    # Calculate variance per channel
    variances = np.var(data, axis=1)
    
    # Calculate z-scores
    mean_var = np.mean(variances)
    std_var = np.std(variances)
    
    if std_var == 0:
        logger.warning("Standard deviation of variances is zero. No bad channels detected.")
        return []
        
    z_scores = (variances - mean_var) / std_var
    
    # Identify bad channels
    bad_mask = np.abs(z_scores) > z_threshold
    bad_channels = [ch_names[i] for i in range(len(ch_names)) if bad_mask[i]]
    
    if bad_channels:
        logger.warning(f"Detected {len(bad_channels)} bad channels: {bad_channels}")
    else:
        logger.info("No bad channels detected.")
        
    return bad_channels

def create_epochs(raw: mne.io.BaseRaw, event_id: Optional[Dict[str, int]] = None, 
                  tmin: float = -1.0, tmax: float = 2.0, 
                  bad_channels: Optional[List[str]] = None) -> mne.Epochs:
    """Create epochs from raw data.
    
    Args:
        raw: MNE Raw object.
        event_id: Dictionary mapping event names to IDs. If None, uses 'stimulus' channel or generates events.
        tmin: Start time relative to event.
        tmax: End time relative to event.
        bad_channels: List of channels to drop before epoching.
        
    Returns:
        MNE Epochs object.
    """
    logger.info(f"Creating epochs with tmin={tmin}, tmax={tmax}")
    
    # Drop bad channels if provided
    if bad_channels:
        logger.info(f"Dropping bad channels: {bad_channels}")
        raw = raw.copy().drop_channels(bad_channels)
    
    # If no events are provided, try to find a stimulus channel or create dummy events
    if event_id is None:
        # Try to find a standard stimulus channel
        stim_channels = [ch for ch in raw.ch_names if 'STI' in ch or 'stim' in ch.lower()]
        if stim_channels:
            logger.info(f"Using stimulus channel: {stim_channels[0]}")
            events = mne.find_events(raw, stim_channel=stim_channels[0], verbose=False)
        else:
            # If no stimulus channel, create dummy events at regular intervals
            logger.warning("No stimulus channel found. Creating dummy events.")
            # Create events every 5 seconds
            event_times = np.arange(tmax, raw.n_times / raw.info['sfreq'] - tmin, 5.0)
            event_samples = (event_times * raw.info['sfreq']).astype(int)
            events = np.column_stack([event_samples, np.zeros_like(event_samples), np.ones_like(event_samples)])
            event_id = {'dummy': 1}
    else:
        # Use provided event_id to find events
        events = mne.find_events(raw, verbose=False)
        
    # Create epochs
    epochs = mne.Epochs(raw, events, event_id=event_id, tmin=tmin, tmax=tmax,
                        baseline=(None, 0), preload=True, verbose=False)
    
    logger.info(f"Created {len(epochs)} epochs")
    return epochs

def save_epochs(epochs: mne.Epochs, output_path: str) -> None:
    """Save epochs to a .fif file.
    
    Args:
        epochs: MNE Epochs object.
        output_path: Path to save the file.
    """
    logger.info(f"Saving epochs to: {output_path}")
    epochs.save(output_path, overwrite=True, verbose=False)
    logger.info(f"Successfully saved epochs to {output_path}")

def process_file(input_path: str, output_dir: str, tmin: float = -1.0, tmax: float = 2.0,
                 z_threshold: float = 5.0, l_freq: float = 1.0, h_freq: float = 45.0) -> str:
    """Process a single EDF file: load, filter, detect bad channels, epoch, and save.
    
    Args:
        input_path: Path to input EDF file.
        output_dir: Directory to save output epochs.
        tmin: Start time relative to event.
        tmax: End time relative to event.
        z_threshold: Z-score threshold for bad channel detection.
        l_freq: Low cutoff frequency for bandpass filter.
        h_freq: High cutoff frequency for bandpass filter.
        
    Returns:
        Path to the saved epochs file.
    """
    logger.info(f"Processing file: {input_path}")
    
    # Load raw data
    raw = load_raw_edf(input_path)
    
    # Apply preprocessing steps
    raw = apply_bandpass_filter(raw, l_freq=l_freq, h_freq=h_freq)
    raw = apply_common_average_reference(raw)
    
    # Detect bad channels
    bad_channels = detect_bad_channels(raw, z_threshold=z_threshold)
    
    # Create epochs
    epochs = create_epochs(raw, tmin=tmin, tmax=tmax, bad_channels=bad_channels)
    
    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Generate output filename
    base_name = Path(input_path).stem
    output_path = str(Path(output_dir) / f"{base_name}_epochs.fif")
    
    # Save epochs
    save_epochs(epochs, output_path)
    
    return output_path

def main():
    """Main entry point for the preprocessing pipeline."""
    logger.info("Starting preprocessing pipeline for T018")
    
    # Ensure output directories exist
    ensure_dirs()
    
    # Define input and output directories
    raw_dir = DATA_RAW
    processed_dir = DATA_PROCESSED
    
    if not raw_dir.exists():
        logger.error(f"Raw data directory not found: {raw_dir}")
        sys.exit(1)
        
    # Get list of EDF files
    edf_files = list(raw_dir.glob("*.edf"))
    if not edf_files:
        logger.warning(f"No EDF files found in {raw_dir}")
        # If no files, create an empty placeholder or exit gracefully
        # Based on task requirements, we expect real data to be present
        sys.exit(0)
        
    logger.info(f"Found {len(edf_files)} EDF files to process")
    
    # Process each file
    output_files = []
    for edf_file in edf_files:
        try:
            output_path = process_file(
                input_path=str(edf_file),
                output_dir=str(processed_dir),
                tmin=-1.0,
                tmax=2.0,
                z_threshold=5.0,
                l_freq=1.0,
                h_freq=45.0
            )
            output_files.append(output_path)
        except Exception as e:
            logger.error(f"Failed to process {edf_file}: {e}")
            # Continue with next file or exit?
            # For robustness, we continue but log the error
            continue
            
    logger.info(f"Processing complete. Generated {len(output_files)} epoch files.")
    logger.info("T018 Implementation: Epoching and bad-channel detection completed.")

if __name__ == "__main__":
    main()
