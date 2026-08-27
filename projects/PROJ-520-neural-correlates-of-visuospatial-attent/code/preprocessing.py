"""
Preprocessing pipeline for EEG data.
Handles filtering, ICA, epoching, and missing electrode handling.
"""
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

# Import logging infrastructure
from logging_config import get_pipeline_logger, log_stage_start, log_stage_end
# Import config for paths
from config import get_paths

# MNE imports for EEG handling
try:
    import mne
except ImportError:
    raise ImportError("MNE-Python is required for EEG preprocessing. Install with: pip install mne")

logger = get_pipeline_logger(__name__)

def fallback_to_landmark_timestamps(raw: 'mne.io.Raw', events: np.ndarray) -> Tuple[np.ndarray, List[str]]:
    """
    Fallback logic for missing event markers.
    Uses landmark timestamps if standard markers are missing.
    
    Args:
        raw: Raw MNE object
        events: Existing events array
        
    Returns:
        Tuple of (updated_events, list_of_fallback_reasons)
    """
    log_stage_start(logger, "fallback_to_landmark_timestamps")
    
    if events is not None and len(events) > 0:
        logger.info("Standard event markers found, no fallback needed.")
        log_stage_end(logger, "fallback_to_landmark_timestamps", status="success")
        return events, []
    
    logger.warning("No event markers found. Attempting fallback to landmark timestamps.")
    # Placeholder logic for landmark detection
    # In a real implementation, this would detect specific peaks or markers in the raw data
    # For now, we return the original (empty) events and a log entry
    fallback_reasons = ["No standard markers found; landmark fallback attempted but no landmarks detected in this stub."]
    
    log_stage_end(logger, "fallback_to_landmark_timestamps", status="fallback_used")
    return events, fallback_reasons

def update_metadata_with_fallback(metadata_path: Path, fallback_details: List[str]) -> None:
    """
    Updates metadata.json with fallback details.
    
    Args:
        metadata_path: Path to metadata.json
        fallback_details: List of strings describing the fallback
    """
    if not metadata_path.exists():
        logger.warning(f"Metadata file not found at {metadata_path}, skipping update.")
        return
        
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
        
    if 'assumptions' not in metadata:
        metadata['assumptions'] = {}
        
    metadata['assumptions']['event_source'] = 'landmark_fallback'
    metadata['assumptions']['fallback_details'] = fallback_details
    
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
        
    logger.info(f"Updated metadata at {metadata_path} with fallback details.")

def handle_missing_electrodes(epochs: 'mne.Epochs', metadata_path: Path) -> Tuple['mne.Epochs', List[str]]:
    """
    Handles missing electrode data by skipping affected electrodes.
    
    Args:
        epochs: MNE Epochs object
        metadata_path: Path to metadata.json for logging skipped electrodes
        
    Returns:
        Tuple of (cleaned_epochs, list_of_skipped_electrodes)
    """
    log_stage_start(logger, "handle_missing_electrodes")
    
    # Get the channel names from the epochs info
    all_channels = epochs.ch_names
    # Get the pickable channels (excluding bads if they are marked)
    # MNE usually handles bad channels via info['bads']
    # We check for channels that are effectively missing or have NaN data
    
    skipped_electrodes = []
    
    # Check for channels with all NaN or very low variance (potential missing data)
    data = epochs.get_data() # shape: (n_epochs, n_channels, n_times)
    
    for idx, ch_name in enumerate(all_channels):
        # Check if this channel has any valid data across all epochs and timepoints
        ch_data = data[:, idx, :]
        if np.all(np.isnan(ch_data)):
            skipped_electrodes.append(ch_name)
            logger.warning(f"Electrode {ch_name} has all NaN data. Marking as bad/skipping.")
        elif np.std(ch_data) < 1e-9:
            # Extremely low variance might indicate a disconnected electrode
            skipped_electrodes.append(ch_name)
            logger.warning(f"Electrode {ch_name} has near-zero variance. Marking as bad/skipping.")
    
    if skipped_electrodes:
        # Mark them as bad in the epochs info
        epochs.info['bads'].extend(skipped_electrodes)
        # Drop them from the epochs object to ensure clean processing
        epochs.drop_channels(skipped_electrodes)
        logger.info(f"Dropped {len(skipped_electrodes)} electrodes: {skipped_electrodes}")
        
        # Update metadata
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            existing_skipped = metadata.get('skipped_electrodes', [])
            existing_skipped.extend(skipped_electrodes)
            # Deduplicate
            metadata['skipped_electrodes'] = list(set(existing_skipped))
            
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            logger.info(f"Updated metadata.json with skipped electrodes: {skipped_electrodes}")
        else:
            logger.error(f"Metadata file not found at {metadata_path}. Cannot log skipped electrodes.")
    else:
        logger.info("No missing or bad electrodes detected.")
    
    log_stage_end(logger, "handle_missing_electrodes", status="success")
    return epochs, skipped_electrodes

def preprocess_pipeline(raw_path: str, events_path: Optional[str] = None) -> 'mne.Epochs':
    """
    Main preprocessing pipeline:
    1. Load raw data
    2. Apply filters (T011)
    3. ICA artifact rejection (T012a, T012b)
    4. Epoch segmentation (T013)
    5. Handle missing electrodes (T016)
    6. Sample size validation (T014)
    7. Fallback for missing markers (T015)
    
    Args:
        raw_path: Path to raw FIF file
        events_path: Optional path to events file
        
    Returns:
        Preprocessed MNE Epochs object
    """
    log_stage_start(logger, "preprocess_pipeline")
    paths = get_paths()
    metadata_path = paths['metadata']
    
    # 1. Load Raw Data
    logger.info(f"Loading raw data from {raw_path}")
    raw = mne.io.read_raw_fif(raw_path, preload=True)
    
    # 2. Load Events
    if events_path and os.path.exists(events_path):
        events = mne.events_from_annotations(raw)[0]
    else:
        events = None
        
    # 3. Handle missing event markers (T015)
    if events is None or len(events) == 0:
        events, fallback_reasons = fallback_to_landmark_timestamps(raw, events)
        update_metadata_with_fallback(metadata_path, fallback_reasons)
        
    # 4. Bandpass and Notch Filter (T011)
    logger.info("Applying bandpass (1-40 Hz) and notch (50 Hz) filters")
    raw.filter(l_freq=1.0, h_freq=40.0, notch_freqs=[50.0])
    
    # 5. ICA Artifact Rejection (T012a, T012b)
    logger.info("Running ICA for artifact rejection")
    ica = mne.preprocessing.ICA(n_components=0.99, random_state=42)
    ica.fit(raw)
    
    # Find EOG and ECG components
    eog_indices, eog_scores = ica.find_bads_eog(raw)
    ecg_indices, ecg_scores = ica.find_bads_ecg(raw)
    
    components_to_drop = list(set(eog_indices + ecg_indices))
    if components_to_drop:
        logger.info(f"Rejecting ICA components: {components_to_drop}")
        ica.exclude = components_to_drop
        ica.apply(raw)
        
        # Log for manual review (T012b)
        log_path = paths['logs'] / "ica_rejection_log.txt"
        with open(log_path, 'w') as f:
            f.write(f"ICA Components Rejected: {components_to_drop}\n")
            f.write(f"EOG Indices: {eog_indices}, Scores: {eog_scores}\n")
            f.write(f"ECG Indices: {ecg_indices}, Scores: {ecg_scores}\n")
    else:
        logger.info("No ICA components rejected automatically.")
        
    # 6. Epoch Segmentation (T013)
    logger.info("Segmenting epochs (2s windows)")
    # Assuming event_id mapping based on task description
    event_id = {'active': 1, 'passive': 2} 
    # If event codes differ, this needs adjustment based on actual data
    epochs = mne.Epochs(raw, events, event_id=event_id, tmin=-1.0, tmax=1.0, 
                        baseline=(None, 0), preload=True, reject=dict(eeg=150e-6))
    
    # 7. Handle Missing Electrodes (T016)
    logger.info("Checking for missing electrode data")
    epochs, skipped = handle_missing_electrodes(epochs, metadata_path)
    
    # 8. Sample Size Validation (T014)
    counts = {k: len(epochs[k]) for k in epochs.event_id}
    min_count = min(counts.values()) if counts else 0
    
    if min_count < 50:
        logger.critical(f"Sample size too low: {min_count} epochs. Halting.")
        raise ValueError(f"Insufficient epochs: {min_count} < 50. Halting pipeline.")
    elif min_count < 100:
        logger.warning(f"Sample size low: {min_count} epochs. Flagging as underpowered.")
        # Update metadata to flag underpowered
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                meta = json.load(f)
            meta['validation_results'] = {
                "min_threshold": 50,
                "flag_threshold": 100,
                "status": "UNDERPOWERED",
                "counts": counts,
                "message": f"WARNING: Underpowered. Counts: {counts}"
            }
            with open(metadata_path, 'w') as f:
                json.dump(meta, f, indent=2)
    
    log_stage_end(logger, "preprocess_pipeline", status="success")
    return epochs

def main():
    """Main entry point for preprocessing."""
    paths = get_paths()
    raw_file = paths['raw'] / "sub-01_task-navigation_eeg.fif"
    
    if not raw_file.exists():
        logger.error(f"Raw data file not found: {raw_file}")
        return
        
    try:
        epochs = preprocess_pipeline(str(raw_file))
        logger.info(f"Preprocessing complete. Total epochs: {len(epochs)}")
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        raise

if __name__ == "__main__":
    main()
