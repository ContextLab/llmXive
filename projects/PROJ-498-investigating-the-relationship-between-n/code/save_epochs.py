"""
T019: Save clean epochs to data/processed/ per subject.

This script iterates over processed subject data, ensures epochs are clean
(no NaNs, valid shape), saves them to disk in FIF format, and updates
the state hashes via update_state_hashes.
"""
import os
import sys
import time
import logging
import mne
import numpy as np
from pathlib import Path

# Import from project modules (API surface)
from config import ensure_directories
from logging_setup import initialize_logging_and_tracking, get_logger
from memory_monitor import monitor_and_ensure_limit, get_current_rss_mb
from update_state_hashes import main as update_hashes_main

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
LOG_FILE = PROJECT_ROOT / "logs" / "processing.log"

def get_subject_ids(raw_dir: Path) -> list:
    """
    Scan data/raw/ for subject directories (e.g., sub-01, sub-02).
    Returns a sorted list of subject IDs.
    """
    if not raw_dir.exists():
        return []
    subjects = []
    for item in sorted(raw_dir.iterdir()):
        if item.is_dir() and item.name.startswith("sub-"):
            subjects.append(item.name)
    return subjects

def load_preprocessed_subject(subject_dir: Path) -> mne.Epochs:
    """
    Load the preprocessed epochs for a subject.
    Expects a file named 'epochs.fif' inside the subject directory.
    """
    epochs_file = subject_dir / "epochs.fif"
    if not epochs_file.exists():
        raise FileNotFoundError(f"Epochs file not found for {subject_dir.name}: {epochs_file}")
    
    # Load with preload=True for cleaning, then drop preload to save memory if needed
    # But we need to check for NaNs first
    epochs = mne.read_epochs(epochs_file, preload=True)
    return epochs

def clean_epochs(epochs: mne.Epochs) -> mne.Epochs:
    """
    Ensure epochs are clean:
    1. Drop epochs with NaNs (if any).
    2. Verify no NaNs remain.
    3. Return the cleaned epochs.
    """
    initial_count = len(epochs)
    
    # Check for NaNs in the data array
    # epochs.get_data() returns (n_epochs, n_channels, n_times)
    data = epochs.get_data()
    nan_mask = np.isnan(data).any(axis=(1, 2))
    
    if nan_mask.any():
        # Drop epochs with NaNs
        epochs.drop(np.where(nan_mask)[0], reason="NaN detected in epoch data")
    
    final_count = len(epochs)
    dropped = initial_count - final_count
    
    if dropped > 0:
        logging.warning(f"Dropped {dropped} epochs due to NaNs for subject {epochs.info['subject_info']}")
    
    # Final check
    if np.isnan(epochs.get_data()).any():
        raise RuntimeError(f"NaNs still present after cleaning for subject {epochs.info['subject_info']}")
    
    return epochs

def save_epochs_to_disk(epochs: mne.Epochs, output_dir: Path):
    """
    Save the cleaned epochs to a FIF file in the processed directory.
    """
    subject_id = epochs.info.get('subject_info', {}).get('subject', 'unknown')
    # If subject info is missing, try to infer from the epochs object or use a generic name
    # mne.Epochs usually doesn't store subject_id directly in info unless set.
    # We'll rely on the directory name passed in or a default.
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / f"{subject_id}_clean_epochs.fif"
    
    # Overwrite if exists
    if output_file.exists():
        output_file.unlink()
    
    # Save with overwrite=True
    epochs.save(output_file, overwrite=True)
    return output_file

def process_and_save_subject(subject_id: str, raw_dir: Path, processed_dir: Path, logger: logging.Logger):
    """
    Load, clean, and save epochs for a single subject.
    """
    subject_dir = raw_dir / subject_id
    if not subject_dir.exists():
        logger.warning(f"Subject directory not found: {subject_dir}")
        return None

    try:
        logger.info(f"Processing subject: {subject_id}")
        
        # Load
        epochs = load_preprocessed_subject(subject_dir)
        
        # Clean
        epochs = clean_epochs(epochs)
        
        # Save
        output_path = save_epochs_to_disk(epochs, processed_dir)
        
        logger.info(f"Saved clean epochs for {subject_id} to {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Failed to process subject {subject_id}: {e}", exc_info=True)
        return None

def main():
    """
    Main entry point for T019.
    """
    # Initialize logging
    logger = initialize_logging_and_tracking(LOG_FILE)
    
    # Ensure directories exist
    ensure_directories()
    
    logger.info("Starting T019: Save clean epochs to data/processed/")
    
    # Get subject list
    subjects = get_subject_ids(RAW_DATA_DIR)
    if not subjects:
        logger.warning("No subjects found in data/raw/. Exiting.")
        return 0
    
    logger.info(f"Found {len(subjects)} subjects to process.")
    
    success_count = 0
    for subj in subjects:
        # Check memory before processing
        monitor_and_ensure_limit(logger)
        
        result = process_and_save_subject(subj, RAW_DATA_DIR, PROCESSED_DIR, logger)
        if result:
            success_count += 1
        
        # Check memory after processing
        monitor_and_ensure_limit(logger)
    
    logger.info(f"T019 Complete. Processed {success_count}/{len(subjects)} subjects.")
    
    if success_count == 0:
        logger.error("No subjects were successfully processed.")
        return 1
    
    # Update state hashes
    logger.info("Updating state hashes...")
    try:
        # Call the main function from update_state_hashes
        update_hashes_main()
    except Exception as e:
        logger.error(f"Failed to update state hashes: {e}", exc_info=True)
        # Don't fail the whole task if hash update fails, but log it
    
    return 0

if __name__ == "__main__":
    sys.exit(main())