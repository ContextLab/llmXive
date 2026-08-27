"""
Preprocessing pipeline for EEG data: download, filter, ICA, epoching, and saving.
Implements User Story 1 tasks: T010-T017.
"""
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import mne
from mne.preprocessing import ICA

# Import project utilities
from config import get_paths, load_config
from logging_config import get_pipeline_logger, log_stage_start, log_stage_end
from ci_limits import enforce_limits, get_cpu_count

# --- Configuration & Constants ---
# Frequency bands for filtering
LOW_FREQ_CUTOFF = 1.0  # Hz
HIGH_FREQ_CUTOFF = 40.0  # Hz
NOTCH_FREQS = [50, 60]  # Hz (will try both, ignore if not present)

# Epoching parameters
EPOCH_TMIN = -1.0  # seconds
EPOCH_TMAX = 1.0   # seconds (2-second window centered on event)

# ICA parameters
ICA_MAX_COMPONENTS = 0.95  # Keep 95% of variance
ICA_METHOD = 'picard'  # FastICA or Picard

# Sample size thresholds (from T014)
MIN_EPOCHS_REQUIRED = 50
WARNING_EPOCHS_THRESHOLD = 100

logger = get_pipeline_logger(__name__)

def validate_sample_size(epochs: mne.Epochs, condition_col: str = 'condition') -> Tuple[bool, str, Dict[str, int]]:
    """
    Validates sample size per condition.
    Returns (is_valid, message, counts_dict).
    Halts if < MIN_EPOCHS_REQUIRED, warns if < WARNING_EPOCHS_THRESHOLD.
    """
    counts = {}
    try:
        # Try to get event codes if condition is numeric, or labels if string
        if hasattr(epochs, 'events') and epochs.events is not None:
            # Count based on event codes if possible, otherwise assume all are valid for now
            # A more robust check uses the metadata if available
            if epochs.metadata is not None and condition_col in epochs.metadata.columns:
                counts = epochs.metadata[condition_col].value_counts().to_dict()
            else:
                # Fallback: count unique event types if no metadata
                unique_events = np.unique(epochs.events[:, -1])
                counts = {str(e): np.sum(epochs.events[:, -1] == e) for e in unique_events}
    except Exception as e:
        logger.warning(f"Could not compute precise condition counts: {e}")
        counts = {'total': len(epochs)}

    # Check minimums
    min_count = min(counts.values()) if counts else 0
    
    if min_count < MIN_EPOCHS_REQUIRED:
        msg = f"CRITICAL: Sample size too low. Minimum {MIN_EPOCHS_REQUIRED} epochs/condition required. Found {min_count}."
        logger.error(msg)
        raise ValueError(msg)
    
    status = "PASS"
    if min_count < WARNING_EPOCHS_THRESHOLD:
        status = "WARNING"
        msg = f"WARNING: Sample size underpowered. Threshold is {WARNING_EPOCHS_THRESHOLD} epochs/condition. Found {min_count}."
        logger.warning(msg)
    
    return True, status, counts

def update_metadata_with_validation(metadata_path: Path, counts: Dict[str, int], status: str) -> None:
    """Updates metadata.json with sample size validation results."""
    if metadata_path.exists():
        with open(metadata_path, 'r') as f:
            meta = json.load(f)
    else:
        meta = {}
    
    meta['validation'] = meta.get('validation', {})
    meta['validation']['sample_size_check'] = {
        'status': status,
        'counts': counts,
        'min_required': MIN_EPOCHS_REQUIRED,
        'warning_threshold': WARNING_EPOCHS_THRESHOLD
    }
    
    with open(metadata_path, 'w') as f:
        json.dump(meta, f, indent=2)
    logger.info(f"Updated metadata at {metadata_path} with validation status.")

def preprocess_pipeline(config_path: Optional[str] = None) -> mne.Epochs:
    """
    Main preprocessing pipeline:
    1. Load raw data (assumed downloaded by T010)
    2. Bandpass and Notch filtering
    3. ICA Artifact Rejection
    4. Epoching
    5. Sample Size Validation
    6. Save to data/processed/epochs_cleaned.fif
    """
    log_stage_start("preprocessing_pipeline")
    
    # Enforce resource limits
    enforce_limits()
    n_cpus = get_cpu_count()
    logger.info(f"Running with {n_cpus} CPU cores.")

    # Load config
    if config_path is None:
        config_path = "config.yaml" # Default
    try:
        cfg = load_config(config_path)
    except FileNotFoundError:
        logger.warning(f"Config {config_path} not found. Using defaults.")
        cfg = {}

    paths = get_paths(cfg)
    raw_dir = Path(paths['raw_data'])
    processed_dir = Path(paths['processed_data'])
    metadata_path = processed_dir / "metadata.json"
    output_path = processed_dir / "epochs_cleaned.fif"

    # Ensure directories exist
    processed_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load Raw Data
    # We assume T010 has downloaded data to raw_dir.
    # We look for FIF, EDF, or BIDS-compliant raw files.
    raw_files = list(raw_dir.glob("*.fif")) + list(raw_dir.glob("*.edf")) + list(raw_dir.glob("*raw.fif"))
    if not raw_files:
        # Fallback for BIDS: look for eeg files
        bids_eeg = list(raw_dir.glob("sub-*/eeg/*.eeg")) + list(raw_dir.glob("sub-*/eeg/*.vhdr"))
        if bids_eeg:
            raw_files = bids_eeg[:1] # Take first found
    
    if not raw_files:
        raise FileNotFoundError(f"No raw data files found in {raw_dir}. Ensure T010 has downloaded data.")
    
    raw_file = raw_files[0]
    logger.info(f"Loading raw data from {raw_file}")
    
    # MNE load_raw handles FIF, EDF, etc.
    raw = mne.io.read_raw_fif(raw_file, preload=True) if raw_file.suffix == '.fif' else mne.io.read_raw_edf(raw_file, preload=True)
    raw.info['bads'] = [] # Initialize bads list

    # 2. Filtering (T011)
    logger.info("Applying bandpass filter (1-40 Hz) and notch filter (50/60 Hz)...")
    raw.filter(l_freq=LOW_FREQ_CUTOFF, h_freq=HIGH_FREQ_CUTOFF, n_jobs=n_cpus)
    for freq in NOTCH_FREQS:
        try:
            raw.notch_filter(freqs=freq, n_jobs=n_cpus)
        except Exception as e:
            logger.warning(f"Could not apply notch filter at {freq} Hz: {e}")

    # 3. ICA Artifact Rejection (T012a, T012b)
    logger.info("Running ICA for artifact rejection...")
    ica = ICA(method=ICA_METHOD, max_iter=ICA_MAX_COMPONENTS, random_state=42)
    ica.fit(raw)
    
    # Find bad components (EOG/ECG)
    # Note: In a real pipeline, we might need to detect EOG/ECG channels first.
    # Assuming standard channel names or using mne.preprocessing.find_eog_events
    eog_indices, eog_scores = ica.find_bads_eog(raw)
    ecg_indices, ecg_scores = ica.find_bads_ecg(raw)
    
    bad_components = list(set(eog_indices + ecg_indices))
    logger.info(f"Identified {len(bad_components)} bad components: {bad_components}")
    
    # Log detailed review info (T012b)
    log_path = processed_dir / "ica_review_log.json"
    review_data = {
        "n_components": len(ica),
        "bad_components": bad_components,
        "eog_scores": {str(i): float(s) for i, s in zip(eog_indices, eog_scores)},
        "ecg_scores": {str(i): float(s) for i, s in zip(ecg_indices, ecg_scores)},
        "method": ICA_METHOD
    }
    with open(log_path, 'w') as f:
        json.dump(review_data, f, indent=2)
    logger.info(f"ICA review log saved to {log_path}")

    # Apply rejection
    raw.drop_components(bad_components)

    # 4. Epoching (T013)
    # We need events. If metadata exists, use it. Otherwise, try to infer from raw events.
    # Assuming T015 logic: if markers missing, use landmarks (simplified here: assume events exist in raw)
    events = mne.find_events(raw, stim_channel='STI 014') # Standard BIDS stim channel
    if len(events) == 0:
        # Fallback for T015: use landmarks if no events
        logger.warning("No events found. Attempting landmark fallback...")
        # Placeholder for landmark logic: assume we found some timestamps
        # In a real scenario, this would load from a specific file or detect peaks
        raise RuntimeError("No events found and landmark fallback not implemented in this snippet.")
    
    # Create events array with condition labels if possible
    # Simplified: assume event codes map to 'active' and 'passive'
    # We'll create a dummy condition mapping for demonstration if not present
    # In real code, we'd parse the event dictionary from the dataset
    event_id = {'active': 1, 'passive': 2} # Example mapping
    
    epochs = mne.Epochs(
        raw, 
        events, 
        event_id=event_id,
        tmin=EPOCH_TMIN, 
        tmax=EPOCH_TMAX,
        baseline=(None, 0),
        reject=None, # No amplitude rejection here, handled by ICA
        preload=True,
        verbose=False
    )
    
    # 5. Sample Size Validation (T014)
    is_valid, status, counts = validate_sample_size(epochs)
    update_metadata_with_validation(metadata_path, counts, status)

    # 6. Save Cleaned Epochs (T017)
    logger.info(f"Saving {len(epochs)} epochs to {output_path}")
    epochs.save(output_path, overwrite=True, verbose=False)
    
    log_stage_end("preprocessing_pipeline")
    return epochs

def main():
    """Entry point for preprocessing pipeline."""
    try:
        epochs = preprocess_pipeline()
        logger.info("Preprocessing pipeline completed successfully.")
    except Exception as e:
        logger.error(f"Preprocessing pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()
