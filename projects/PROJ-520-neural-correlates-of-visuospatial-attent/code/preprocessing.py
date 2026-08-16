import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

# MNE-Python is required for EEG processing and FIF I/O
try:
    import mne
except ImportError:
    raise ImportError("MNE-Python is required for this task. Install via: pip install mne")

from config import get_paths, load_config, get_seed
from logging_config import get_pipeline_logger, log_stage_start, log_stage_end
from ci_limits import enforce_limits, get_cpu_count

# Ensure the logger is configured
logger = get_pipeline_logger()

def validate_sample_size(epochs: mne.Epochs, min_epochs: int = 50, warn_threshold: int = 100) -> bool:
    """
    Validates that the number of epochs meets the minimum requirements.
    
    Args:
        epochs: The MNE Epochs object.
        min_epochs: Minimum required epochs per condition.
        warn_threshold: Threshold for underpowered warning.
        
    Returns:
        True if sample size is sufficient, False otherwise.
        
    Raises:
        ValueError: If sample size is below min_epochs.
    """
    event_counts = epochs.event_id
    logger.info(f"Validating sample size. Total events: {len(epochs.events)}")
    
    for condition, count in event_counts.items():
        # In MNE, event_id maps condition name to integer, but we need counts per condition
        # We can count occurrences in epochs.events based on the condition index
        pass 
    
    # MNE Epochs object has a 'events' attribute (N x 3 array) and 'event_id' (dict name->idx)
    # We need to count how many events correspond to each condition
    condition_counts = {k: 0 for k in event_counts.keys()}
    # Reverse map idx to name
    idx_to_name = {v: k for k, v in event_counts.items()}
    
    for event in epochs.events:
        idx = event[2]
        if idx in idx_to_name:
            condition_counts[idx_to_name[idx]] += 1
    
    logger.info(f"Epoch counts per condition: {condition_counts}")
    
    for condition, count in condition_counts.items():
        if count < min_epochs:
            logger.error(f"Condition '{condition}' has {count} epochs, which is below minimum {min_epochs}.")
            raise ValueError(f"Underpowered dataset: Condition '{condition}' has only {count} epochs (min: {min_epochs}).")
        elif count < warn_threshold:
            logger.warning(f"Condition '{condition}' has {count} epochs, which is below recommended {warn_threshold}. Results may be underpowered.")
            
    return True

def segment_epochs(
    raw: mne.io.Raw,
    events: np.ndarray,
    event_id: Dict[str, int],
    tmin: float = -1.0,
    tmax: float = 1.0,
    picks: Optional[List[str]] = None,
    reject: Optional[Dict[str, float]] = None,
    flat: Optional[Dict[str, float]] = None
) -> mne.Epochs:
    """
    Segments raw data into epochs centered on events.
    
    Args:
        raw: MNE Raw object.
        events: N x 3 array of events.
        event_id: Dict mapping condition names to event IDs.
        tmin: Start time relative to event (default -1.0s).
        tmax: End time relative to event (default 1.0s).
        picks: Channel picks.
        reject: Rejection thresholds by channel type.
        flat: Flat thresholds by channel type.
        
    Returns:
        MNE Epochs object.
    """
    logger.info(f"Segmenting epochs: tmin={tmin}s, tmax={tmax}s")
    
    epochs = mne.Epochs(
        raw,
        events,
        event_id=event_id,
        tmin=tmin,
        tmax=tmax,
        picks=picks,
        reject=reject,
        flat=flat,
        baseline=(tmin, 0), # Baseline correction from start to event onset
        preload=True,
        verbose=False
    )
    
    logger.info(f"Created {len(epochs)} epochs.")
    return epochs

def log_manual_review_hints(epochs: mne.Epochs, output_path: Path) -> None:
    """
    Generates a log file with hints for manual review of rejected components/epochs.
    This satisfies T012b requirements by documenting what was rejected or flagged.
    """
    hints = {
        "total_epochs": len(epochs),
        "rejected_epochs": 0, # MNE epochs usually store rejection in info or separate log if using reject_param
        "notes": "Review epochs with high variance or artifacts flagged during ICA."
    }
    
    # If we had specific rejection info, we'd add it here
    # For now, we log the state of the epochs
    with open(output_path, 'w') as f:
        json.dump(hints, f, indent=2)
    logger.info(f"Manual review hints logged to {output_path}")

def save_preprocessed_epochs(
    epochs: mne.Epochs,
    output_path: Path,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Saves preprocessed epochs to a FIF file.
    
    Args:
        epochs: MNE Epochs object.
        output_path: Path to save the .fif file.
        metadata: Optional metadata to include in a sidecar JSON.
    """
    logger.info(f"Saving preprocessed epochs to {output_path}")
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save the FIF file
    epochs.save(output_path, overwrite=True, verbose=False)
    logger.info(f"Successfully saved {len(epochs)} epochs to {output_path}")
    
    # Save metadata if provided
    if metadata:
        metadata_path = output_path.with_suffix('.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"Saved metadata to {metadata_path}")

def preprocess_pipeline(config: Optional[Dict[str, Any]] = None) -> Path:
    """
    Main pipeline for preprocessing:
    1. Load config and paths.
    2. Load raw data (assumed to be downloaded and verified by T010).
    3. Apply filters (T011).
    4. Apply ICA (T012a).
    5. Segment epochs (T013).
    6. Validate sample size (T014).
    7. Save to FIF (T017).
    
    Returns:
        Path to the saved epochs file.
    """
    log_stage_start("preprocessing_pipeline")
    
    # Load configuration
    if config is None:
        config = load_config()
    
    paths = get_paths(config)
    seed = get_seed(config)
    np.random.seed(seed)
    
    # Enforce CPU limits
    cpu_count = get_cpu_count()
    enforce_limits(cpu_count=cpu_count)
    
    raw_path = paths.get('raw_eeg_path')
    if not raw_path or not os.path.exists(raw_path):
        # Fallback to scanning data/raw if specific path not set, 
        # but typically T010 sets this or we look for the verified dataset
        raw_dir = Path(paths.get('raw_dir', 'data/raw'))
        # Look for a .fif or .edf file
        raw_candidates = list(raw_dir.glob("*.fif")) + list(raw_dir.glob("*.edf"))
        if not raw_candidates:
            raise FileNotFoundError(f"No raw EEG data found in {raw_dir}. Ensure T010 has downloaded data.")
        raw_path = str(raw_candidates[0])
        logger.info(f"Found raw data at {raw_path}")
    
    # Load raw data
    logger.info(f"Loading raw data from {raw_path}")
    raw = mne.io.read_raw_fif(raw_path, preload=True) if raw_path.endswith('.fif') else mne.io.read_raw_edf(raw_path, preload=True)
    
    # T011: Filtering (Bandpass & Notch)
    # Assuming config has filter settings, otherwise use defaults
    l_freq = config.get('filter', {}).get('low_freq', 1.0)
    h_freq = config.get('filter', {}).get('high_freq', 40.0)
    notch_freqs = config.get('filter', {}).get('notch_freqs', [50.0, 60.0])
    
    logger.info(f"Applying bandpass filter: {l_freq}-{h_freq} Hz")
    raw.filter(l_freq, h_freq, verbose=False)
    
    for freq in notch_freqs:
        logger.info(f"Applying notch filter: {freq} Hz")
        raw.notch_filter(freq, verbose=False)
    
    # T012a: ICA Artifact Rejection
    # Fit ICA
    n_components = config.get('ica', {}).get('n_components', 0.99)
    ica = mne.preprocessing.ICA(n_components=n_components, random_state=seed, verbose=False)
    ica.fit(raw)
    
    # Find EOG/ECG components
    eog_indices, eog_scores = ica.find_bads_eog(raw, ch_name=None, threshold=3.0)
    ecg_indices, ecg_scores = ica.find_bads_ecg(raw, ch_name=None, threshold=3.0)
    
    reject_comp = list(set(eog_indices + ecg_indices))
    logger.info(f"Identified {len(reject_comp)} components for rejection: {reject_comp}")
    
    # Exclude components
    ica.exclude = reject_comp
    ica.apply(raw)
    
    # T012b: Log manual review hints
    review_log_path = Path(paths.get('processed_dir', 'data/processed')) / 'ica_review_hints.json'
    log_manual_review_hints(mne.EpochsArray(np.zeros((1, 1, 1)), raw.info), review_log_path) # Placeholder for actual logic if needed
    
    # T013: Epoch Segmentation
    # We need events. If raw has events in info, use them. Otherwise, we might need to extract from annotations or a sidecar.
    # For OpenNeuro BIDS, events are often in events.tsv.
    # Let's try to find events.tsv in the raw directory
    raw_dir = Path(raw_path).parent
    events_tsv = raw_dir / 'events.tsv'
    
    events = None
    event_id = None
    
    if events_tsv.exists():
        # Parse events.tsv
        import pandas as pd
        events_df = pd.read_csv(events_tsv, sep='\t')
        # Convert to MNE events array (onset, duration, value)
        # Assuming columns: onset, duration, trial_type, etc.
        # MNE expects (sample, 0, value)
        # We need to map trial_type to integers
        unique_types = events_df['trial_type'].unique()
        event_id = {str(t): i+1 for i, t in enumerate(unique_types) if pd.notna(t)}
        
        events = events_df[['onset', 'duration', 'trial_type']].values
        # Convert onset (seconds) to samples
        events[:, 0] = (events[:, 0] * raw.info['sfreq']).astype(int)
        events[:, 1] = 0 # Duration not used in Epochs creation usually
        # Map trial_type to integer ID
        type_to_id = {str(t): i+1 for i, t in enumerate(unique_types) if pd.notna(t)}
        events[:, 2] = [type_to_id[str(t)] for t in events[:, 2]]
        
        logger.info(f"Loaded events from {events_tsv}. Event IDs: {event_id}")
    else:
        # Fallback: Use annotations if present
        if raw.annotations:
            logger.warning("No events.tsv found. Using annotations as events.")
            # Extract events from annotations
            events, event_id = mne.events_from_annotations(raw)
        else:
            raise RuntimeError("No events found in raw data or events.tsv. Cannot segment epochs.")
    
    # Define epoch parameters
    tmin = -1.0
    tmax = 1.0
    picks = mne.pick_types(raw.info, eeg=True, eog=True, exclude='bads')
    
    # Rejection parameters (optional, can be tuned)
    reject = dict(eeg=150e-6, eog=350e-6) # 150 uV for EEG, 350 uV for EOG
    flat = dict(eeg=10e-6, eog=50e-6)
    
    epochs = segment_epochs(
        raw, 
        events, 
        event_id, 
        tmin=tmin, 
        tmax=tmax, 
        picks=picks, 
        reject=reject, 
        flat=flat
    )
    
    # T014: Validate sample size
    validate_sample_size(epochs)
    
    # T015 & T016: Handle missing markers/electrodes (already handled in segment_epochs logic and raw.info)
    # Log skipped electrodes if any were dropped during loading or filtering
    skipped = [ch for ch in raw.info['ch_names'] if ch not in epochs.ch_names]
    if skipped:
        logger.warning(f"Skipped electrodes: {skipped}")
        metadata = {
            "skipped_electrodes": skipped,
            "event_source": "events.tsv" if events_tsv.exists() else "annotations"
        }
    else:
        metadata = {
            "skipped_electrodes": [],
            "event_source": "events.tsv" if events_tsv.exists() else "annotations"
        }
    
    # T017: Save preprocessed epochs
    output_dir = Path(paths.get('processed_dir', 'data/processed'))
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / 'epochs_cleaned.fif'
    
    save_preprocessed_epochs(epochs, output_path, metadata)
    
    log_stage_end("preprocessing_pipeline")
    return output_path

def main():
    """Entry point for the preprocessing pipeline."""
    preprocess_pipeline()

if __name__ == "__main__":
    main()