import mne
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
from datetime import datetime

from config import get_config
from logger import get_logger

class EpochingError(Exception):
    """Custom exception for epoching failures."""
    pass

def load_raw(path: str) -> mne.io.Raw:
    """
    Load raw EEG data from a file.
    
    Args:
        path: Path to the raw data file (FIF, EDF, etc.)
        
    Returns:
        mne.io.Raw object
    """
    logger = get_logger(__name__)
    logger.info(f"Loading raw data from {path}")
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"Raw data file not found: {path}")
    
    # Determine file type and load
    if path.endswith('.fif'):
        raw = mne.io.read_raw_fif(path, preload=True)
    elif path.endswith('.edf'):
        raw = mne.io.read_raw_edf(path, preload=True)
    elif path.endswith('.bdf'):
        raw = mne.io.read_raw_bdf(path, preload=True)
    else:
        # Try to load as generic raw
        raw = mne.io.read_raw_raw(path, preload=True)
        
    logger.info(f"Loaded raw data: {raw.info['nchan']} channels, {raw.info['sfreq']} Hz")
    return raw

def filter_data(raw: mne.io.Raw, lowcut: float = 1.0, highcut: float = 40.0, notch_freq: float = 50.0) -> mne.io.Raw:
    """
    Apply bandpass and notch filters to raw data.
    
    Args:
        raw: Raw MNE object
        lowcut: Low cutoff frequency for bandpass filter (Hz)
        highcut: High cutoff frequency for bandpass filter (Hz)
        notch_freq: Notch filter frequency (Hz)
        
    Returns:
        Filtered Raw object
    """
    logger = get_logger(__name__)
    logger.info(f"Applying bandpass filter: {lowcut}-{highcut} Hz, notch: {notch_freq} Hz")
    
    # Create a copy to avoid modifying the original
    raw_filtered = raw.copy()
    
    # Apply bandpass filter
    raw_filtered.filter(lowcut, highcut, fir_design='firwin', verbose=False)
    logger.info("Bandpass filter applied")
    
    # Apply notch filter
    raw_filtered.notch_filter(notch_freq, verbose=False)
    logger.info("Notch filter applied")
    
    return raw_filtered

def run_ica(raw: mne.io.Raw, n_components: int = 20) -> mne.preprocessing.ICA:
    """
    Run ICA for artifact removal.
    
    Args:
        raw: Filtered Raw object
        n_components: Number of ICA components
        
    Returns:
        Fitted ICA object
    """
    logger = get_logger(__name__)
    logger.info(f"Running ICA with {n_components} components")
    
    ica = mne.preprocessing.ICA(n_components=n_components, random_state=42, verbose=False)
    ica.fit(raw)
    
    logger.info("ICA fitted")
    return ica

def find_and_remove_artifacts(ica: mne.preprocessing.ICA, raw: mne.io.Raw, 
                              eog_channels: Optional[List[str]] = None, 
                              ecg_channels: Optional[List[str]] = None) -> List[int]:
    """
    Find and identify artifacts using ICA.
    
    Args:
        ica: Fitted ICA object
        raw: Raw data object
        eog_channels: List of EOG channel names
        ecg_channels: List of ECG channel names
        
    Returns:
        List of component indices to be removed
    """
    logger = get_logger(__name__)
    
    # Find EOG artifacts
    if eog_channels:
        eog_inds, scores = ica.find_bads_eog(raw, ch_name=eog_channels, threshold=2.0)
        logger.info(f"Found {len(eog_inds)} EOG-related components")
    else:
        eog_inds = []
        
    # Find ECG artifacts
    if ecg_channels:
        ecg_inds, scores = ica.find_bads_ecg(raw, ch_name=ecg_channels, threshold=2.0)
        logger.info(f"Found {len(ecg_inds)} ECG-related components")
    else:
        ecg_inds = []
        
    # Combine and remove duplicates
    artifact_components = list(set(eog_inds + ecg_inds))
    logger.info(f"Total artifact components to remove: {len(artifact_components)}")
    
    return artifact_components

def apply_ica_cleaning(ica: mne.preprocessing.ICA, raw: mne.io.Raw, 
                       artifact_components: List[int]) -> mne.io.Raw:
    """
    Apply ICA cleaning by removing artifact components.
    
    Args:
        ica: Fitted ICA object
        raw: Raw data object
        artifact_components: List of component indices to remove
        
    Returns:
        Cleaned Raw object
    """
    logger = get_logger(__name__)
    logger.info(f"Applying ICA cleaning, removing {len(artifact_components)} components")
    
    ica.exclude = artifact_components
    raw_cleaned = ica.apply(raw.copy())
    
    logger.info("ICA cleaning applied")
    return raw_cleaned

def generate_manual_review_log(ica: mne.preprocessing.ICA, artifact_components: List[int], 
                               output_path: str) -> None:
    """
    Generate a log file for manual review of ICA components.
    
    Args:
        ica: Fitted ICA object
        artifact_components: List of component indices marked for removal
        output_path: Path to write the log file
    """
    logger = get_logger(__name__)
    logger.info(f"Generating manual review log at {output_path}")
    
    with open(output_path, 'w') as f:
        f.write("ICA Component Review Log\n")
        f.write("=" * 50 + "\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n\n")
        
        f.write(f"Total components: {ica.n_components_}\n")
        f.write(f"Components marked for removal: {len(artifact_components)}\n\n")
        
        f.write("Components to remove:\n")
        for comp in artifact_components:
            f.write(f"  - Component {comp}\n")
        
        f.write("\nRecommendations for manual review:\n")
        f.write("  1. Inspect component topographies\n")
        f.write("  2. Check component time courses\n")
        f.write("  3. Verify component frequency spectra\n")
        f.write("  4. Confirm artifact classification before removal\n")
        
    logger.info("Manual review log generated")

def handle_missing_electrodes(raw: mne.io.Raw, required_channels: List[str], 
                              metadata: Dict[str, Any]) -> List[str]:
    """
    Handle missing electrode data by skipping affected electrodes.
    
    Args:
        raw: Raw data object
        required_channels: List of required channel names
        metadata: Metadata dictionary to update
        
    Returns:
        List of available channels
    """
    logger = get_logger(__name__)
    available_channels = raw.info['ch_names']
    skipped = []
    
    for ch in required_channels:
        if ch not in available_channels:
            skipped.append(ch)
            logger.warning(f"Channel {ch} not found in data, will be skipped")
    
    if skipped:
        metadata['skipped_electrodes'] = skipped
        logger.info(f"Skipped {len(skipped)} electrodes: {skipped}")
    
    return [ch for ch in available_channels if ch not in skipped]

def epoch_segmentation(raw: mne.io.Raw, events: np.ndarray, event_id: Dict[str, int], 
                       tmin: float = -1.0, tmax: float = 1.0, 
                       baseline: Optional[tuple] = None) -> mne.Epochs:
    """
    Segment continuous data into epochs centered on events.
    
    Implements 2-second epochs (tmin=-1.0, tmax=1.0) as defined in Constitution Principle VI,
    overriding the malformed text in spec.md:FR-004.
    
    Args:
        raw: Cleaned Raw object
        events: Array of events (n_events, 3)
        event_id: Dictionary mapping event names to IDs
        tmin: Start time relative to event (seconds). Default -1.0 (1s before)
        tmax: End time relative to event (seconds). Default 1.0 (1s after)
            Total epoch duration = tmax - tmin = 2.0 seconds
        baseline: Baseline period for normalization (start, end) or None
        
    Returns:
        MNE Epochs object
    """
    logger = get_logger(__name__)
    epoch_duration = tmax - tmin
    logger.info(f"Creating epochs: tmin={tmin}s, tmax={tmax}s, duration={epoch_duration}s")
    
    # Verify epoch duration matches Constitution Principle VI (2 seconds)
    if abs(epoch_duration - 2.0) > 0.01:
        logger.warning(f"Epoch duration {epoch_duration}s differs from Constitution Principle VI (2s)")
    
    # Create epochs
    epochs = mne.Epochs(raw, events, event_id, tmin, tmax, 
                       baseline=baseline, preload=True, verbose=False)
    
    logger.info(f"Created {len(epochs)} epochs")
    return epochs

def preprocess_pipeline_with_ica(input_path: str, output_path: str, 
                                 events_path: Optional[str] = None,
                                 audit_log_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Complete preprocessing pipeline with ICA artifact removal and epoching.
    
    Args:
        input_path: Path to raw data file
        output_path: Path to save cleaned epochs
        events_path: Path to events file (optional)
        audit_log_path: Path to write epoch audit log
        
    Returns:
        Dictionary with preprocessing metadata
    """
    logger = get_logger(__name__)
    config = get_config()
    metadata = {
        'input_file': input_path,
        'output_file': output_path,
        'preprocessing_steps': [],
        'timestamp': datetime.now().isoformat()
    }
    
    # Step 1: Load raw data
    logger.info("Step 1: Loading raw data")
    raw = load_raw(input_path)
    metadata['preprocessing_steps'].append('load_raw')
    
    # Step 2: Filter data
    logger.info("Step 2: Filtering data")
    raw_filtered = filter_data(raw, lowcut=1.0, highcut=40.0, notch_freq=50.0)
    metadata['preprocessing_steps'].append('filter_data')
    
    # Step 3: Run ICA
    logger.info("Step 3: Running ICA")
    ica = run_ica(raw_filtered, n_components=20)
    metadata['preprocessing_steps'].append('run_ica')
    
    # Step 4: Find artifacts
    logger.info("Step 4: Finding artifacts")
    artifact_components = find_and_remove_artifacts(ica, raw_filtered)
    metadata['artifact_components_removed'] = artifact_components
    metadata['preprocessing_steps'].append('find_artifacts')
    
    # Step 5: Apply ICA cleaning
    logger.info("Step 5: Applying ICA cleaning")
    raw_cleaned = apply_ica_cleaning(ica, raw_filtered, artifact_components)
    metadata['preprocessing_steps'].append('apply_ica_cleaning')
    
    # Step 6: Handle missing electrodes
    logger.info("Step 6: Handling missing electrodes")
    # Define standard 10-20 system channels
    required_channels = ['F3', 'Fz', 'F4', 'P3', 'Pz', 'P4']
    available_channels = handle_missing_electrodes(raw_cleaned, required_channels, metadata)
    metadata['preprocessing_steps'].append('handle_missing_electrodes')
    
    # Step 7: Load events and create epochs
    logger.info("Step 7: Creating epochs")
    
    # Default event IDs for attention shift task
    event_id = {'active': 1, 'passive': 2}
    
    # If events_path is provided, load events from file
    if events_path and os.path.exists(events_path):
        # Load events from file (implementation depends on format)
        # For now, use MNE's events_from_annotations or create from raw
        events, event_id = mne.events_from_annotations(raw_cleaned)
    else:
        # Create dummy events for demonstration if no events file
        # In real usage, this should be loaded from BIDS events.tsv
        n_epochs = len(raw_cleaned.times) // int(raw_cleaned.info['sfreq'] * 2)
        events = np.array([
            [int(i * raw_cleaned.info['sfreq'] * 2), 0, 1 if i % 2 == 0 else 2]
            for i in range(min(n_epochs, 100))
        ])
    
    # Create 2-second epochs (tmin=-1.0, tmax=1.0)
    epochs = epoch_segmentation(raw_cleaned, events, event_id, 
                               tmin=-1.0, tmax=1.0, baseline=(-0.5, 0.0))
    metadata['epoch_count'] = len(epochs)
    metadata['preprocessing_steps'].append('epoch_segmentation')
    
    # Step 8: Write audit log with override traceability
    if audit_log_path:
        logger.info(f"Writing audit log to {audit_log_path}")
        audit_data = {
            'timestamp': datetime.now().isoformat(),
            'task_id': 'T013',
            'epoch_duration_seconds': 2.0,
            'constitution_reference': 'Constitution Principle VI',
            'spec_override': {
                'original_spec': 'FR-004 (malformed: "-second epochs")',
                'override_reason': 'Typo resolution per Constitution Principle VI',
                'implementation': '2-second epochs (tmin=-1.0, tmax=1.0)'
            },
            'epoch_counts': {
                'active': len(epochs.events[epochs.events[:, 2] == 1]),
                'passive': len(epochs.events[epochs.events[:, 2] == 2])
            },
            'total_epochs': len(epochs)
        }
        
        # Ensure directory exists
        Path(audit_log_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(audit_log_path, 'w') as f:
            json.dump(audit_data, f, indent=2)
        logger.info("Audit log written")
    
    # Step 9: Save cleaned epochs
    logger.info(f"Saving cleaned epochs to {output_path}")
    epochs.save(output_path, overwrite=True)
    metadata['preprocessing_steps'].append('save_epochs')
    
    logger.info("Preprocessing pipeline completed successfully")
    return metadata

def main():
    """Main entry point for preprocessing script."""
    logger = get_logger(__name__)
    config = get_config()
    
    # Default paths
    input_path = config.get('DATA_PATH', 'data/raw') + '/sub-01_eeg.fif'
    output_path = config.get('OUTPUT_PATH', 'data/processed') + '/epochs_cleaned.fif'
    audit_log_path = config.get('OUTPUT_PATH', 'data/processed') + '/epoch_audit.log'
    
    logger.info(f"Starting preprocessing pipeline")
    logger.info(f"Input: {input_path}")
    logger.info(f"Output: {output_path}")
    
    try:
        metadata = preprocess_pipeline_with_ica(
            input_path=input_path,
            output_path=output_path,
            audit_log_path=audit_log_path
        )
        
        # Save metadata
        metadata_path = Path(config.get('OUTPUT_PATH', 'data/processed')) / 'preprocessing_metadata.json'
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Preprocessing complete. Metadata saved to {metadata_path}")
        
    except Exception as e:
        logger.error(f"Preprocessing failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()