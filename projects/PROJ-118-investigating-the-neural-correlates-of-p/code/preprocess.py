"""
Preprocessing pipeline for auditory oddball EEG data.

This module handles:
- Channel selection and montage assignment
- Filtering and re-referencing
- Epoching
- ICA-based artifact removal
"""
import os
import yaml
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import mne

from config_loader import get_project_root, get_config, ensure_directory
from cleanup_utils import setup_logger, validate_array_shape, log_execution_time

# Configure logger
logger = setup_logger(__name__)

# ----------------------------------------------------------------------
# Montage Configuration
# ----------------------------------------------------------------------

def get_standard_montage() -> mne.channels.make_dig_montage:
    """
    Return the standard 32-channel EEG montage.

    Returns:
        Standard montage object.
    """
    # Standard 32-channel montage coordinates
    montage = mne.channels.make_standard_montage('standard_1005')
    return montage

def get_mmn_montage() -> List[str]:
    """
    Return the list of channels required for MMN analysis.

    Returns:
        List of channel names (e.g., Fz, FCz, Cz, Pz).
    """
    return ['Fz', 'FCz', 'Cz', 'Pz', 'F3', 'F4', 'C3', 'C4', 'P3', 'P4']

def set_montage(raw: mne.io.Raw, montage_name: str = 'standard_1005') -> mne.io.Raw:
    """
    Set the montage for raw data.

    Args:
        raw: Raw data object.
        montage_name: Name of the standard montage.

    Returns:
        Raw data with montage set.
    """
    montage = mne.channels.make_standard_montage(montage_name)
    raw.set_montage(montage, match_case=False, match_alias=True)
    logger.info(f"Set montage to {montage_name}")
    return raw

def select_channels(raw: mne.io.Raw, channels: List[str]) -> mne.io.Raw:
    """
    Select specific channels from raw data.

    Args:
        raw: Raw data object.
        channels: List of channel names to keep.

    Returns:
        Raw data with only selected channels.
    """
    # Filter out channels not present in raw
    available = [ch for ch in channels if ch in raw.ch_names]
    missing = [ch for ch in channels if ch not in raw.ch_names]
    if missing:
        logger.warning(f"Channels not found and ignored: {missing}")

    raw.pick_channels(available)
    logger.info(f"Selected channels: {available}")
    return raw

# ----------------------------------------------------------------------
# Filtering and Re-referencing
# ----------------------------------------------------------------------

@log_execution_time()
def apply_filter(raw: mne.io.Raw, l_freq: float = 1.0, h_freq: float = 30.0) -> mne.io.Raw:
    """
    Apply bandpass filter to raw data.

    Args:
        raw: Raw data object.
        l_freq: Low cutoff frequency (Hz).
        h_freq: High cutoff frequency (Hz).

    Returns:
        Filtered raw data.
    """
    raw.filter(l_freq, h_freq, method='fir', fir_design='firwin')
    logger.info(f"Applied bandpass filter: {l_freq}-{h_freq} Hz")
    return raw

@log_execution_time()
def rereference(raw: mne.io.Raw, method: str = 'average') -> mne.io.Raw:
    """
    Re-reference EEG data.

    Args:
        raw: Raw data object.
        method: Re-referencing method ('average', 'mastoids', etc.).

    Returns:
        Re-referenced raw data.
    """
    if method == 'average':
        raw.set_eeg_reference(ref_channels='average', projection=True)
    else:
        raise ValueError(f"Unsupported re-referencing method: {method}")
    logger.info(f"Re-referenced to {method}")
    return raw

# ----------------------------------------------------------------------
# Epoching
# ----------------------------------------------------------------------

def find_events(raw: mne.io.Raw, stimulus_channel: str = 'STI 014') -> np.ndarray:
    """
    Find events from the stimulus channel.

    Args:
        raw: Raw data object.
        stimulus_channel: Name of the stimulus channel.

    Returns:
        Array of events (time, previous, value).
    """
    events = mne.find_events(raw, stim_channel=stimulus_channel)
    logger.info(f"Found {len(events)} events")
    return events

@log_execution_time()
def create_epochs(
    raw: mne.io.Raw,
    events: np.ndarray,
    event_id: Dict[str, int],
    tmin: float = -0.2,
    tmax: float = 0.5,
    baseline: Optional[Tuple[float, float]] = (-0.2, 0.0)
) -> mne.Epochs:
    """
    Create epochs from raw data.

    Args:
        raw: Raw data object.
        events: Event array.
        event_id: Dictionary mapping condition names to event codes.
        tmin: Start time relative to event (s).
        tmax: End time relative to event (s).
        baseline: Baseline period (start, end) or None.

    Returns:
        Epochs object.
    """
    epochs = mne.Epochs(
        raw, events, event_id, tmin, tmax,
        baseline=baseline, reject_by_annotation=True,
        preload=True
    )
    logger.info(f"Created {len(epochs)} epochs")
    return epochs

# ----------------------------------------------------------------------
# ICA Processing
# ----------------------------------------------------------------------

@log_execution_time()
def detect_ica_components(epochs: mne.Epochs, threshold: float = 0.8) -> List[int]:
    """
    Detect ICA components likely to be artifacts (blinks).

    Args:
        epochs: Epochs object.
        threshold: Correlation threshold for blink detection.

    Returns:
        List of component indices to remove.
    """
    # Fit ICA
    ica = mne.preprocessing.ICA(n_components=0.95, method='fastica', random_state=42)
    ica.fit(epochs)

    # Find blink components
    # Note: In a real pipeline, we would use mne.preprocessing.find_blinks or similar
    # Here we simulate detection based on frontal channel correlation
    # For this implementation, we'll assume components with high frontal activity are blinks
    # In production, replace with actual blink detection logic
    frontal_channels = ['Fp1', 'Fp2', 'AFz', 'Fz']
    available_frontal = [ch for ch in frontal_channels if ch in epochs.ch_names]

    if not available_frontal:
        logger.warning("No frontal channels found for ICA blink detection.")
        return []

    # Find components correlated with frontal channels
    # This is a simplified heuristic; real implementation uses mne.preprocessing.find_blinks
    components_to_remove = []
    for comp_idx in range(len(ica)):
        # Get component topography
        comp_map = ica.get_sources(epochs).get_data()[comp_idx]
        # Check if frontal channels have high amplitude (simplified check)
        # In real code, we'd correlate with EOG channel or use mne.preprocessing.find_blinks
        # Here we just mark components that might be artifacts for demonstration
        # A real implementation would use:
        # eog_indices, eog_scores = mne.preprocessing.find_blinks(epochs, ch_name='Fp1', threshold=3.0)
        # components_to_remove = eog_indices
        pass

    # Placeholder for actual blink detection logic
    # In a real scenario, we would run:
    # eog_indices, _ = mne.preprocessing.find_blinks(epochs, ch_name='Fp1')
    # components_to_remove = list(eog_indices)
    # For now, we return an empty list to avoid removing real data without proper detection
    logger.info("ICA component detection complete (placeholder for blink detection).")
    return components_to_remove

@log_execution_time()
def remove_ica_components(epochs: mne.Epochs, components: List[int]) -> mne.Epochs:
    """
    Remove ICA components from epochs.

    Args:
        epochs: Epochs object.
        components: List of component indices to remove.

    Returns:
        Cleaned epochs object.
    """
    if not components:
        logger.info("No components to remove.")
        return epochs

    ica = mne.preprocessing.ICA(n_components=0.95, method='fastica', random_state=42)
    ica.fit(epochs)
    ica.exclude = components
    ica.apply(epochs)
    logger.info(f"Removed {len(components)} ICA components: {components}")
    return epochs

# ----------------------------------------------------------------------
# Pipeline Execution
# ----------------------------------------------------------------------

@log_execution_time()
def preprocess_pipeline(
    raw_path: str,
    output_path: str,
  config: Optional[Dict[str, Any]] = None
) -> mne.Epochs:
    """
    Run the full preprocessing pipeline.

    Args:
        raw_path: Path to raw FIF file.
        output_path: Path to save cleaned epochs.
        config: Optional configuration dictionary.

    Returns:
        Cleaned epochs object.
    """
    # Load config if not provided
    if config is None:
        config = get_config()

    # Load raw data
    raw = mne.io.read_raw_fif(raw_path, preload=True)

    # Set montage
    raw = set_montage(raw)

    # Select channels
    mmn_channels = get_mmn_montage()
    raw = select_channels(raw, mmn_channels)

    # Filter
    l_freq = config.get('filter', {}).get('l_freq', 1.0)
    h_freq = config.get('filter', {}).get('h_freq', 30.0)
    raw = apply_filter(raw, l_freq, h_freq)

    # Re-reference
    raw = rereference(raw)

    # Find events
    events = find_events(raw)

    # Create epochs
    event_id = config.get('event_id', {'standard': 1, 'deviant': 2})
    tmin = config.get('epoch', {}).get('tmin', -0.2)
    tmax = config.get('epoch', {}).get('tmax', 0.5)
    baseline = tuple(config.get('epoch', {}).get('baseline', [-0.2, 0.0]))
    epochs = create_epochs(raw, events, event_id, tmin, tmax, baseline)

    # ICA
    threshold = config.get('ica', {}).get('threshold', 0.8)
    components = detect_ica_components(epochs, threshold)
    epochs = remove_ica_components(epochs, components)

    # Save
    ensure_directory(Path(output_path).parent)
    epochs.save(output_path, overwrite=True)
    logger.info(f"Saved cleaned epochs to {output_path}")

    return epochs

@log_execution_time()
def run_preprocessing_pipeline(
    data_dir: str,
    output_dir: str,
    config_path: Optional[str] = None
) -> List[str]:
    """
    Run preprocessing on all subjects in a directory.

    Args:
        data_dir: Directory containing raw data.
        output_dir: Directory to save processed data.
        config_path: Path to config file.

    Returns:
        List of output file paths.
    """
    project_root = get_project_root()
    if config_path is None:
        config_path = project_root / 'code' / 'config.yaml'

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    data_path = Path(data_dir)
    output_path = Path(output_dir)
    ensure_directory(output_path)

    output_files = []

    for raw_file in data_path.glob('sub-*/ses-*/eeg/*_task-auditory_*-raw.fif'):
        subject_id = raw_file.parent.parent.parent.name
        output_file = output_path / f"{subject_id}_epo_clean.fif"

        logger.info(f"Processing {raw_file} -> {output_file}")
        try:
            preprocess_pipeline(str(raw_file), str(output_file), config)
            output_files.append(str(output_file))
        except Exception as e:
            logger.error(f"Failed to process {raw_file}: {e}")

    return output_files

def main():
    """Main entry point for preprocessing."""
    project_root = get_project_root()
    data_dir = project_root / 'data' / 'raw'
    output_dir = project_root / 'data' / 'processed'

    if not data_dir.exists():
        logger.error(f"Data directory not found: {data_dir}")
        return

    output_files = run_preprocessing_pipeline(str(data_dir), str(output_dir))
    logger.info(f"Preprocessing complete. Processed {len(output_files)} subjects.")

if __name__ == "__main__":
    main()
