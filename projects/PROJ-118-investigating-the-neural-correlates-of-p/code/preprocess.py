"""
Preprocessing pipeline for auditory oddball EEG data.
Implements filtering, ICA, and epoching for MMN analysis.
"""
import os
import yaml
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import mne
import numpy as np

from config_loader import get_project_root, get_config, ensure_directory
from data_utils import load_raw_data, get_subject_ids

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_standard_montage() -> mne.channels.DigMontage:
    """Return the standard 32-channel EEG montage."""
    # Using standard 10-20 montage available in MNE
    montage = mne.channels.make_standard_montage('standard_1005')
    return montage

def get_mmn_montage() -> List[str]:
    """Return the list of channels required for MMN analysis (Fz, FCz, Cz, Pz, etc.)."""
    # Standard montage for MMN analysis focusing on frontal/central electrodes
    mmn_channels = [
        'Fz', 'FCz', 'Cz', 'Pz', 'F3', 'F4', 'FC3', 'FC4', 
        'C3', 'C4', 'CP3', 'CP4', 'P3', 'P4', 'POz', 'F7', 
        'F8', 'FT7', 'FT8', 'T7', 'T8', 'TP7', 'TP8', 'P7', 
        'P8', 'O1', 'O2', 'Fpz', 'Fp1', 'Fp2', 'AFz', 'POz'
    ]
    return mmn_channels

def set_montage(raw: mne.io.Raw, montage: mne.channels.DigMontage) -> mne.io.Raw:
    """Set the montage on the raw data."""
    raw.set_montage(montage, match_case=False, match_alias=True, on_missing='warn')
    return raw

def select_channels(raw: mne.io.Raw, channel_list: List[str]) -> mne.io.Raw:
    """Select only the specified channels from the raw data."""
    available = [ch for ch in channel_list if ch in raw.ch_names]
    missing = [ch for ch in channel_list if ch not in raw.ch_names]
    if missing:
        logger.warning(f"Channels not found in data: {missing}")
    raw.pick_channels(available)
    return raw

def load_config_and_validate() -> Dict[str, Any]:
    """Load and validate the configuration file."""
    project_root = get_project_root()
    config_path = project_root / 'code' / 'config.yaml'
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config

def find_events(raw: mne.io.Raw, config: Dict[str, Any]) -> np.ndarray:
    """Find events in the raw data based on stimulus channel."""
    stim_channel = config.get('stimulus_channel', 'STI 014')
    if stim_channel not in raw.ch_names:
        # Try to find any stimulus channel
        stim_channels = [ch for ch in raw.ch_names if 'STI' in ch or 'stim' in ch.lower()]
        if stim_channels:
            stim_channel = stim_channels[0]
            logger.info(f"Using stimulus channel: {stim_channel}")
        else:
            raise ValueError("No stimulus channel found in the data")
    
    events = mne.find_events(raw, stim_channel=stim_channel)
    return events

def detect_ica_components(raw: mne.io.Raw, config: Dict[str, Any], epochs: Optional[mne.Epochs] = None) -> List[int]:
    """
    Detect ICA components to remove (blinks, eye artifacts).
    
    Args:
        raw: Raw data (continuous or early epoched)
        config: Configuration dictionary
        epochs: Optional epochs object if already created
    
    Returns:
        List of component indices to remove
    """
    n_components = config.get('ica_components', 20)
    threshold = config.get('ica_threshold', 0.8)
    frontal_channels = ['Fz', 'F3', 'F4', 'FCz']
    
    # Run ICA on continuous data or early epoched data
    if epochs is not None:
        data_for_ica = epochs.get_data()
    else:
        data_for_ica = raw.get_data()
    
    ica = mne.preprocessing.ICA(n_components=n_components, random_state=42)
    
    if epochs is not None:
        ica.fit(epochs)
    else:
        ica.fit(raw)
    
    # Find components correlating with frontal channels
    component_scores = []
    for idx in range(ica.n_components_):
        # Get the component topography
        comp_topo = ica.get_components()[idx]
        
        # Check correlation with frontal channels
        frontal_correlations = []
        for ch_name in frontal_channels:
            if ch_name in raw.ch_names:
              ch_idx = raw.ch_names.index(ch_name)
              frontal_correlations.append(abs(comp_topo[ch_idx]))
        
        if frontal_correlations:
            avg_correlation = np.mean(frontal_correlations)
            component_scores.append((idx, avg_correlation))
    
    # Select components above threshold
    components_to_remove = [idx for idx, score in component_scores if score >= threshold]
    
    # Also check for frontal topography (high variance in frontal regions)
    for idx in range(ica.n_components_):
        comp_topo = ica.get_components()[idx]
        if idx not in components_to_remove:
            # Check if frontal channels have high variance
            frontal_values = [comp_topo[raw.ch_names.index(ch)] for ch in frontal_channels if ch in raw.ch_names]
            if frontal_values and np.std(frontal_values) > 0.5:  # Threshold for frontal topography
                components_to_remove.append(idx)
    
    components_to_remove = list(set(components_to_remove))  # Remove duplicates
    logger.info(f"Detected {len(components_to_remove)} ICA components to remove: {components_to_remove}")
    
    return components_to_remove

def remove_ica_components(raw: mne.io.Raw, ica: mne.preprocessing.ICA, components: List[int]) -> mne.io.Raw:
    """Remove specified ICA components from the raw data."""
    if not components:
        logger.info("No ICA components to remove")
        return raw
    
    ica.exclude = components
    raw_clean = ica.apply(raw)
    logger.info(f"Removed {len(components)} ICA components from data")
    return raw_clean

def create_epochs(raw: mne.io.Raw, events: np.ndarray, config: Dict[str, Any], 
                 event_id: Optional[Dict[str, int]] = None) -> mne.Epochs:
    """
    Create epochs from raw data for standard and deviant conditions.
    
    Args:
        raw: Cleaned raw data (after ICA)
        events: Event array from find_events
        config: Configuration dictionary
        event_id: Dictionary mapping condition names to event codes
    
    Returns:
        Epochs object with standard and deviant conditions
    """
    # Get epoch parameters from config
    tmin = config.get('epoch_tmin', -0.2)  # -200ms baseline
    tmax = config.get('epoch_tmax', 0.6)   # 600ms post-stimulus
    baseline = config.get('baseline', (tmin, 0))
    
    # Default event IDs for auditory oddball paradigm
    if event_id is None:
        event_id = {
            'standard': 1,  # Standard tone (e.g., 1000 Hz)
            'deviant': 2    # Deviant tone (e.g., 2000 Hz)
        }
    
    # Filter events to only include standard and deviant
    relevant_events = []
    for event in events:
        if event[2] in event_id.values():
            relevant_events.append(event)
    
    if not relevant_events:
        raise ValueError("No standard or deviant events found in the data")
    
    logger.info(f"Found {len(relevant_events)} events for epoching")
    
    # Create epochs
    epochs = mne.Epochs(
        raw, 
        np.array(relevant_events), 
        event_id=event_id,
        tmin=tmin, 
        tmax=tmax,
        baseline=baseline,
        reject=None,  # No rejection at this stage
        preload=True
    )
    
    logger.info(f"Created epochs: {len(epochs)} total epochs")
    logger.info(f"Standard epochs: {len(epochs['standard'])}")
    logger.info(f"Deviant epochs: {len(epochs['deviant'])}")
    
    return epochs

def preprocess_pipeline(subject_id: str, config: Dict[str, Any]) -> mne.Epochs:
    """
    Run the full preprocessing pipeline for a single subject.
    
    Args:
        subject_id: Subject identifier (e.g., 'sub-01')
        config: Configuration dictionary
    
    Returns:
        Preprocessed epochs object
    """
    project_root = get_project_root()
    raw_dir = project_root / 'data' / 'raw'
    processed_dir = project_root / 'data' / 'processed'
    ensure_directory(processed_dir)
    
    # Load raw data
    logger.info(f"Loading raw data for {subject_id}")
    raw = load_raw_data(raw_dir, subject_id)
    
    # Set montage
    montage = get_standard_montage()
    raw = set_montage(raw, montage)
    
    # Select channels
    mmn_channels = get_mmn_montage()
    raw = select_channels(raw, mmn_channels)
    
    # Filter data (bandpass 1-30 Hz)
    l_freq = config.get('filter_l_freq', 1.0)
    h_freq = config.get('filter_h_freq', 30.0)
    raw.filter(l_freq, h_freq, method='iir', fir_design='firwin')
    logger.info(f"Applied bandpass filter: {l_freq}-{h_freq} Hz")
    
    # Re-reference to common average
    raw = raw.set_eeg_reference('average', projection=False)
    logger.info("Re-referenced to common average")
    
    # Find events
    events = find_events(raw, config)
    
    # Run ICA on continuous data
    logger.info("Running ICA for artifact detection")
    ica = mne.preprocessing.ICA(n_components=config.get('ica_components', 20), random_state=42)
    ica.fit(raw)
    
    # Detect components to remove
    components_to_remove = detect_ica_components(raw, config)
    
    # Remove ICA components
    if components_to_remove:
        raw = remove_ica_components(raw, ica, components_to_remove)
        # Log the components removed
        log_path = processed_dir / f'{subject_id}_ica_log.txt'
        with open(log_path, 'w') as f:
            f.write(f"Subject: {subject_id}\n")
            f.write(f"Components removed: {components_to_remove}\n")
            f.write(f"Number of components: {len(components_to_remove)}\n")
    
    # Create epochs
    epochs = create_epochs(raw, events, config)
    
    # Save epochs to processed directory
    output_path = processed_dir / f'{subject_id}_epo_raw.fif'
    epochs.save(output_path, overwrite=True)
    logger.info(f"Saved epochs to {output_path}")
    
    return epochs

def run_preprocessing_pipeline():
    """Run the preprocessing pipeline for all subjects."""
    config = load_config_and_validate()
    project_root = get_project_root()
    raw_dir = project_root / 'data' / 'raw'
    
    # Get all subject IDs
    subject_ids = get_subject_ids(raw_dir)
    
    logger.info(f"Found {len(subject_ids)} subjects to process")
    
    for subject_id in subject_ids:
        try:
            logger.info(f"Processing {subject_id}...")
            epochs = preprocess_pipeline(subject_id, config)
            logger.info(f"Successfully processed {subject_id}")
        except Exception as e:
            logger.error(f"Failed to process {subject_id}: {str(e)}")
            raise

if __name__ == '__main__':
    run_preprocessing_pipeline()
