import os
import sys
import logging
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
import mne
import numpy as np

# Import config for frequency bands and thresholds
try:
    from utils.config import BANDS, LOWER_FREQ_HZ
except ImportError:
    # Fallback if utils.config is not in path during direct execution
    BANDS = ['delta', 'theta', 'alpha', 'beta', 'gamma']
    LOWER_FREQ_HZ = 1.0

from utils.logging_setup import get_logger

logger = get_logger(__name__)

# Constants for epoching and bad channel detection
EPOCH_DURATION_SEC = 2.0
EPOCH_TMIN = -0.2
BAD_CHANNEL_ZSCORE_THRESHOLD = 5.0

def load_raw_edf(file_path: Path) -> mne.io.Raw:
    """
    Load an EDF file using MNE-Python.
    
    Args:
        file_path: Path to the EDF file.
        
    Returns:
        Loaded mne.io.Raw object.
    """
    logger.info(f"Loading EDF file: {file_path}")
    if not file_path.exists():
        raise FileNotFoundError(f"EDF file not found: {file_path}")
    
    raw = mne.io.read_raw_edf(file_path, preload=True, verbose=False)
    logger.info(f"Loaded raw data with shape: {raw.get_data().shape}, duration: {raw.times[-1]:.2f}s")
    return raw

def apply_common_average_reference(raw: mne.io.Raw) -> mne.io.Raw:
    """
    Apply Common Average Reference (CAR) to the raw data.
    
    Args:
        raw: Input raw object.
        
    Returns:
        Raw object with CAR applied.
    """
    logger.info("Applying Common Average Reference (CAR)")
    raw.set_eeg_reference('average', projection=False)
    return raw

def apply_bandpass_filter(raw: mne.io.Raw, l_freq: float = 1.0, h_freq: float = 45.0) -> mne.io.Raw:
    """
    Apply band-pass filter (1-45 Hz) to the raw data.
    
    Args:
        raw: Input raw object.
        l_freq: Low frequency cutoff.
        h_freq: High frequency cutoff.
        
    Returns:
        Filtered raw object.
    """
    logger.info(f"Applying band-pass filter: {l_freq}-{h_freq} Hz")
    raw.filter(l_freq=l_freq, h_freq=h_freq, method='fir', n_jobs=1, verbose=False)
    return raw

def detect_bad_channels(raw: mne.io.Raw) -> List[str]:
    """
    Detect bad channels based on z-score of channel variance.
    
    Criteria: Channels with z-score of variance > BAD_CHANNEL_ZSCORE_THRESHOLD are marked bad.
    
    Args:
        raw: Input raw object.
        
    Returns:
        List of bad channel names.
    """
    logger.info("Detecting bad channels using z-score of variance")
    data = raw.get_data()
    ch_names = raw.ch_names
    
    # Calculate variance for each channel
    channel_variances = np.var(data, axis=1)
    
    # Calculate z-scores
    mean_var = np.mean(channel_variances)
    std_var = np.std(channel_variances)
    
    if std_var == 0:
        logger.warning("Standard deviation of channel variances is zero. No bad channels detected.")
        return []
        
    z_scores = (channel_variances - mean_var) / std_var
    
    bad_channels = []
    for i, z in enumerate(z_scores):
        if abs(z) > BAD_CHANNEL_ZSCORE_THRESHOLD:
            bad_channels.append(ch_names[i])
            logger.warning(f"Channel {ch_names[i]} marked as bad (z-score: {z:.2f})")
    
    if bad_channels:
        logger.info(f"Detected {len(bad_channels)} bad channels: {bad_channels}")
    else:
        logger.info("No bad channels detected based on variance z-score.")
        
    return bad_channels

def create_epochs(raw: mne.io.Raw, event_id: Optional[Dict[str, int]] = None, 
                  tmin: float = EPOCH_TMIN, tmax: float = EPOCH_DURATION_SEC,
                  bad_channels: Optional[List[str]] = None) -> mne.Epochs:
    """
    Create epochs from raw data with automated bad channel detection.
    
    Args:
        raw: Preprocessed raw object.
        event_id: Dictionary mapping event descriptions to IDs. If None, creates dummy events.
        tmin: Start time relative to event.
        tmax: End time relative to event.
        bad_channels: List of channels to exclude. If None, detected automatically.
        
    Returns:
        mne.Epochs object.
    """
    logger.info(f"Creating epochs from {tmin}s to {tmax}s relative to events")
    
    # Detect bad channels if not provided
    if bad_channels is None:
        bad_channels = detect_bad_channels(raw)
    
    # Mark bad channels
    if bad_channels:
        raw.info['bads'] = bad_channels
        logger.info(f"Marked channels as bad in raw info: {raw.info['bads']}")
    
    # If no events provided, create dummy events for continuous data
    if event_id is None:
        logger.info("No event_id provided. Creating dummy events for continuous data.")
        # Create events at regular intervals
        events = mne.make_fixed_length_events(raw, duration=EPOCH_DURATION_SEC, start=abs(tmin))
        event_id = {'dummy': 1}
    else:
        events = mne.find_events(raw, stim_channel='STI 014', verbose=False)
        if len(events) == 0:
            logger.warning("No events found. Creating dummy events.")
            events = mne.make_fixed_length_events(raw, duration=EPOCH_DURATION_SEC, start=abs(tmin))
            event_id = {'dummy': 1}
    
    # Create epochs
    epochs = mne.Epochs(raw, events, event_id, tmin, tmax, 
                        baseline=(None, 0), reject=None, flat=None,
                        preload=True, verbose=False)
    
    logger.info(f"Created {len(epochs)} epochs. Shape: {epochs.get_data().shape}")
    
    # Drop bad epochs based on peak-to-peak amplitude (optional safety check)
    # Using a relatively lenient threshold to avoid dropping too much data
    reject_criteria = dict(eeg=150e-6)  # 150 uV
    epochs.drop_bad(reject=reject_criteria)
    logger.info(f"After dropping bad epochs: {len(epochs)} epochs remain")
    
    return epochs

def save_epochs(epochs: mne.Epochs, output_path: Path) -> None:
    """
    Save epochs to a FIF file.
    
    Args:
        epochs: Epochs object to save.
        output_path: Path to save the FIF file.
    """
    logger.info(f"Saving epochs to: {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    epochs.save(output_path, overwrite=True, verbose=False)
    logger.info(f"Epochs saved successfully to {output_path}")

def process_file(input_path: Path, output_dir: Path) -> Optional[Path]:
    """
    Process a single EDF file: load, filter, epoch, and save.
    
    Args:
        input_path: Path to input EDF file.
        output_dir: Directory to save output epochs.
        
    Returns:
        Path to output FIF file, or None if processing failed.
    """
    try:
        # Load
        raw = load_raw_edf(input_path)
        
        # Preprocess
        raw = apply_common_average_reference(raw)
        raw = apply_bandpass_filter(raw, l_freq=LOWER_FREQ_HZ, h_freq=45.0)
        
        # Detect bad channels and create epochs
        epochs = create_epochs(raw)
        
        # Save
        stem = input_path.stem
        output_path = output_dir / f"{stem}_epochs.fif"
        save_epochs(epochs, output_path)
        
        return output_path
        
    except Exception as e:
        logger.error(f"Failed to process {input_path}: {e}", exc_info=True)
        return None

def main():
    """
    Main entry point for the preprocessing pipeline.
    Processes all EDF files in data/raw/ and saves epochs to data/processed/.
    """
    logger.info("Starting preprocessing pipeline for epoching and bad channel detection")
    
    # Define paths
    raw_dir = Path("data/raw")
    processed_dir = Path("data/processed")
    
    if not raw_dir.exists():
        logger.error(f"Raw data directory not found: {raw_dir}")
        sys.exit(1)
    
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all EDF files
    edf_files = list(raw_dir.glob("*.edf"))
    if not edf_files:
        logger.warning(f"No EDF files found in {raw_dir}")
        sys.exit(0)
    
    logger.info(f"Found {len(edf_files)} EDF files to process")
    
    # Process each file
    successful_outputs = []
    for edf_file in edf_files:
        logger.info(f"Processing: {edf_file.name}")
        output_path = process_file(edf_file, processed_dir)
        if output_path:
            successful_outputs.append(output_path)
    
    logger.info(f"Pipeline completed. Successfully processed {len(successful_outputs)}/{len(edf_files)} files.")
    
    if not successful_outputs:
        logger.warning("No files were successfully processed.")
        sys.exit(1)
    
    # Log summary of bad channels detected across files
    logger.info("Preprocessing pipeline finished successfully.")

if __name__ == "__main__":
    main()
