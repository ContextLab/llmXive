"""
T017: Implement band-pass filtering (1-45 Hz) and common-average referencing.
Reads raw EDF files from data/raw/, processes them, and writes epochs to data/processed/.
"""
import os
import sys
import logging
from pathlib import Path
from typing import List, Optional

import mne
import numpy as np
import pandas as pd

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.config import ensure_dirs
from utils.logging_setup import get_logger, log_resource_usage

# Constants from config or defaults
BANDPASS_LOW = 1.0
BANDPASS_HIGH = 45.0
# Standard MNE montage for 10-20 system if not present in file
STANDARD_MONTAGE = 'standard_1005'

logger = get_logger(__name__)

def load_raw_edf(file_path: Path) -> mne.io.BaseRaw:
    """Load an EDF file into MNE Raw object."""
    logger.info(f"Loading raw data from: {file_path}")
    try:
        raw = mne.io.read_raw_edf(file_path, preload=True, verbose=False)
        # If montage is missing, set a standard one
        if raw.info['ch_names'] and not raw.get_montage():
            try:
                montage = mne.channels.make_standard_montage(STANDARD_MONTAGE)
                raw.set_montage(montage, match_case=False, match_alias=True, on_missing='ignore')
            except Exception as e:
                logger.warning(f"Could not set standard montage: {e}")
        return raw
    except Exception as e:
        logger.error(f"Failed to load {file_path}: {e}")
        raise

def apply_common_average_reference(raw: mne.io.BaseRaw) -> mne.io.BaseRaw:
    """Apply Common Average Reference (CAR) to the data."""
    logger.info("Applying Common Average Reference (CAR)...")
    # MNE's set_eeg_reference with 'average' handles this
    # We need to ensure EEG channels are identified
    raw.set_eeg_reference(ref_channels='average', projection=False)
    return raw

def apply_bandpass_filter(raw: mne.io.BaseRaw, l_freq: float, h_freq: float) -> mne.io.BaseRaw:
    """Apply band-pass filter."""
    logger.info(f"Applying band-pass filter: {l_freq}-{h_freq} Hz")
    # Use MNE's filter function
    # Note: raw is already preloaded from load_raw_edf
    raw.filter(l_freq=l_freq, h_freq=h_freq, method='fir', n_jobs=1, verbose=False)
    return raw

def create_epochs(raw: mne.io.BaseRaw, tmin: float = -1.0, tmax: float = 2.0) -> mne.Epochs:
    """
    Create fixed-duration epochs.
    Since T017 depends on T013/T015 which verify alignment but might not have event markers,
    we create continuous epochs or assume a trigger channel 'STI 014' if present.
    If no events, we segment the continuous data into fixed windows.
    """
    logger.info("Creating epochs...")
    
    # Check for standard trigger channel
    events = None
    event_id = None
    
    if 'STI 014' in raw.ch_names:
        logger.info("Found trigger channel 'STI 014'. Extracting events.")
        events, event_id = mne.find_events(raw, stim_channel='STI 014', verbose=False)
    
    if events is not None and len(events) > 0:
        # Standard epoching with events
        epochs = mne.Epochs(raw, events, event_id, tmin=tmin, tmax=tmax, 
                            baseline=(tmin, 0), preload=True, verbose=False)
    else:
        logger.warning("No trigger channel found. Creating fixed-duration epochs from continuous data.")
        # Create a dummy event every 10 seconds if no triggers
        sfreq = raw.info['sfreq']
        duration = tmax - tmin
        # Generate dummy events
        n_events = int((raw.times[-1] - duration) / duration)
        if n_events < 1:
            n_events = 1
        
        dummy_events = np.zeros((n_events, 3), dtype=int)
        dummy_events[:, 0] = np.arange(0, n_events * int(duration * sfreq), int(duration * sfreq))
        dummy_events[:, 1] = 0
        dummy_events[:, 2] = 1
        
        epochs = mne.Epochs(raw, dummy_events, event_id={1: 1}, tmin=tmin, tmax=tmax,
                            baseline=(tmin, 0), preload=True, verbose=False)
    
    return epochs

def save_epochs(epochs: mne.Epochs, output_path: Path):
    """Save epochs to FIF file."""
    logger.info(f"Saving epochs to: {output_path}")
    epochs.save(output_path, overwrite=True, verbose=False)

def process_file(input_path: Path, output_dir: Path) -> Optional[Path]:
    """Process a single file: Load -> CAR -> Filter -> Epoch -> Save."""
    try:
        # 1. Load
        raw = load_raw_edf(input_path)
        
        # 2. Common Average Reference
        raw = apply_common_average_reference(raw)
        
        # 3. Band-pass filter (1-45 Hz)
        raw = apply_bandpass_filter(raw, BANDPASS_LOW, BANDPASS_HIGH)
        
        # 4. Epoching (fixed duration)
        epochs = create_epochs(raw)
        
        # 5. Save
        output_filename = input_path.stem + "_processed.fif"
        output_path = output_dir / output_filename
        save_epochs(epochs, output_path)
        
        return output_path
    except Exception as e:
        logger.error(f"Error processing {input_path}: {e}")
        return None

def main():
    """Main entry point for T017."""
    ensure_dirs()
    
    raw_dir = PROJECT_ROOT / "data" / "raw"
    processed_dir = PROJECT_ROOT / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all EDF files
    edf_files = list(raw_dir.glob("*.edf"))
    if not edf_files:
        logger.warning(f"No .edf files found in {raw_dir}. Skipping preprocessing.")
        return
    
    logger.info(f"Found {len(edf_files)} EDF files to process.")
    
    processed_files = []
    for f_path in edf_files:
        result = process_file(f_path, processed_dir)
        if result:
            processed_files.append(result)
            log_resource_usage()
    
    logger.info(f"Preprocessing complete. {len(processed_files)} files written to {processed_dir}.")

if __name__ == "__main__":
    main()
