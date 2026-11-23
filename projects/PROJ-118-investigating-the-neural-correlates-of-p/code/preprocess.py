"""
Preprocessing pipeline for auditory oddball EEG data.

This module handles:
- Channel selection and montage assignment
- Filtering and re-referencing
- ICA-based blink artifact detection & removal
- Epoching
- Saving of the subsampled raw data (T002 requirement) and ICA‑cleaned continuous data
  (T004 requirement).
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
    Return the standard 32‑channel EEG montage.

    Returns:
        Standard montage object.
    """
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
    available = [ch for ch in channels if ch in raw.ch_names]
    missing = [ch for ch in channels if ch not in raw.ch_names]
    if missing:
        logger.warning(f"Channels not found and ignored: {missing}")

    raw.pick_channels(available)
    logger.info(f"Selected channels: {available}")
    return raw

# ----------------------------------------------------------------------
# Filtering and Re‑referencing
# ----------------------------------------------------------------------

@log_execution_time
def apply_filter(raw: mne.io.Raw, l_freq: float = 1.0, h_freq: float = 30.0) -> mne.io.Raw:
    """
    Apply band‑pass filter to raw data.

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

@log_execution_time
def rereference(raw: mne.io.Raw, method: str = 'average') -> mne.io.Raw:
    """
    Re‑reference EEG data.

    Args:
        raw: Raw data object.
        method: Re‑referencing method ('average', 'mastoids', etc.).

    Returns:
        Re‑referenced raw data.
    """
    if method == 'average':
        raw.set_eeg_reference(ref_channels='average', projection=True)
    else:
        raise ValueError(f"Unsupported re‑referencing method: {method}")
    logger.info(f"Re‑referenced to {method}")
    return raw

# ----------------------------------------------------------------------
# ICA Detection & Removal
# ----------------------------------------------------------------------

@log_execution_time
def detect_ica_components(
    raw: mne.io.Raw,
    threshold: float = 0.8,
    frontal_channels: List[str] = ['Fz', 'FCz']
) -> List[int]:
    """
    Detect ICA components that likely correspond to eye‑blink artifacts.

    The detection is based on Pearson correlation between each component's
    time‑course and the average signal of the specified frontal channels.
    Components with absolute correlation greater than ``threshold`` are
    flagged for removal.

    Args:
        raw: Continuous Raw object (already filtered and re‑referenced).
        threshold: Correlation threshold for blink detection.
        frontal_channels: List of channel names to use for correlation.

    Returns:
        List of component indices to remove.
    """
    # Fit ICA on the continuous data
    ica = mne.preprocessing.ICA(
        n_components=0.95,
        method='fastica',
        random_state=42
    )
    ica.fit(raw)

    # Get component time‑courses
    sources = ica.get_sources(raw).get_data()  # shape (n_components, n_times)

    # Extract frontal channel data (average across the requested channels)
    picks = mne.pick_channels(raw.info['ch_names'], frontal_channels)
    if not picks:
        logger.warning("No frontal channels found for ICA correlation; no components will be removed.")
        return []

    frontal_data = raw.get_data(picks=picks)  # shape (n_frontal, n_times)
    frontal_avg = frontal_data.mean(axis=0)   # shape (n_times,)

    # Compute absolute Pearson correlation for each component
    removed = []
    for comp_idx in range(sources.shape[0]):
        comp_ts = sources[comp_idx, :]
        # Pearson correlation
        corr = np.corrcoef(comp_ts, frontal_avg)[0, 1]
        if np.isnan(corr):
            continue
        if abs(corr) > threshold:
            removed.append(comp_idx)

    logger.info(f"ICA detection: {len(removed)} component(s) exceed correlation threshold {threshold}")
    return removed

@log_execution_time
def remove_ica_components(raw: mne.io.Raw, components: List[int]) -> mne.io.Raw:
    """
    Remove the specified ICA components from the continuous data.

    Args:
        raw: Continuous Raw object.
        components: List of component indices to exclude.

    Returns:
        Cleaned Raw object.
    """
    if not components:
        logger.info("No ICA components to remove.")
        return raw

    ica = mne.preprocessing.ICA(
        n_components=0.95,
        method='fastica',
        random_state=42
    )
    ica.fit(raw)
    ica.exclude = components
    ica.apply(raw)
    logger.info(f"Removed ICA components: {components}")
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

@log_execution_time
def create_epochs(
    raw: mne.io.Raw,
    events: np.ndarray,
    event_id: Dict[str, int],
    tmin: float = -0.2,
    tmax: float = 0.5,
    baseline: Optional[Tuple[float, float]] = (-0.2, 0.0),
    config: Optional[Dict[str, Any]] = None
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
        config: Optional configuration dict (currently unused).

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
# Pipeline Execution
# ----------------------------------------------------------------------

@log_execution_time
def preprocess_subject(subject_id: str, config: Dict[str, Any]) -> mne.Epochs:
    """
    Run preprocessing for a single subject.

    This function now fulfills both:
    - T002 (subsampled, filtered, re‑referenced continuous data)
    - T004 (ICA blink‑component detection & removal)

    Steps:
    1. Load raw FIF file.
    2. Set standard montage.
    3. Select MMN‑relevant channels.
    4. Apply band‑pass filter.
    5. Re‑reference to common average.
    6. Save the filtered continuous data (subsampled_raw.fif).
    7. Run ICA detection on the continuous data.
    8. Remove detected components and save ICA‑cleaned continuous file
       (subsampled_clean.fif) plus a log of removed component indices.
    9. Find events, create epochs, and save cleaned epochs per subject.

    Args:
        subject_id: Identifier of the subject (e.g., ``sub-01``).
        config: Configuration dictionary.

    Returns:
        Cleaned MNE Epochs object.
    """
    project_root = get_project_root()
    raw_dir = project_root / 'data' / 'raw'
    processed_dir = project_root / 'data' / 'processed'
    ensure_directory(processed_dir)

    # Locate the raw FIF file for the given subject
    raw_pattern = raw_dir / f"{subject_id}/**/*_task-auditory*_raw.fif"
    raw_files = list(raw_pattern.glob())
    if not raw_files:
        raise FileNotFoundError(f"No raw FIF file found for subject {subject_id}")
    raw_path = raw_files[0]

    # Load raw data
    raw = mne.io.read_raw_fif(str(raw_path), preload=True)

    # Set montage
    raw = set_montage(raw)

    # Select MMN channels
    mmn_channels = get_mmn_montage()
    raw = select_channels(raw, mmn_channels)

    # Filter
    l_freq = config.get('filter', {}).get('lowcut', 1.0)
    h_freq = config.get('filter', {}).get('highcut', 30.0)
    raw = apply_filter(raw, l_freq, h_freq)

    # Re‑reference
    raw = rereference(raw, method='average')

    # Save subsampled, filtered, re‑referenced continuous data (T002 output)
    subsampled_path = processed_dir / 'subsampled_raw.fif'
    raw.save(str(subsampled_path), overwrite=True)
    logger.info(f"Saved subsampled raw data to {subsampled_path}")

    # ------------------------------------------------------------------
    # ICA detection & removal (T004)
    # ------------------------------------------------------------------
    ica_threshold = config.get('ica', {}).get('threshold', 0.8)
    components_to_remove = detect_ica_components(raw, ica_threshold)

    # Log removed component indices
    ica_log_path = processed_dir / 'ica_removed.log'
    with ica_log_path.open('w') as log_f:
        if components_to_remove:
            log_f.write('Removed ICA components: ' + ','.join(map(str, components_to_remove)) + '\\n')
        else:
            log_f.write('No ICA components removed.\\n')
    logger.info(f"ICA removal log written to {ica_log_path}")

    # Apply removal
    raw = remove_ica_components(raw, components_to_remove)

    # Save ICA‑cleaned continuous data (T004 output)
    cleaned_path = processed_dir / 'subsampled_clean.fif'
    raw.save(str(cleaned_path), overwrite=True)
    logger.info(f"Saved ICA‑cleaned continuous data to {cleaned_path}")

    # ------------------------------------------------------------------
    # Epoching (uses the ICA‑cleaned continuous data)
    # ------------------------------------------------------------------
    events = find_events(raw)

    event_id = config.get('event_id', {'standard': 1, 'deviant': 2})
    tmin = config.get('epoch', {}).get('tmin', -0.2)
    tmax = config.get('epoch', {}).get('tmax', 0.6)  # 600 ms as per spec
    baseline = tuple(config.get('epoch', {}).get('baseline', [-0.2, 0.0]))
    epochs = create_epochs(raw, events, event_id, tmin, tmax, baseline, config=config)

    # Save cleaned epochs for the subject
    epochs_path = processed_dir / f"{subject_id}_epo_raw.fif"
    epochs.save(str(epochs_path), overwrite=True)
    logger.info(f"Saved cleaned epochs to {epochs_path}")

    return epochs

@log_execution_time
def run_preprocessing_pipeline(
    data_dir: Optional[str] = None,
    output_dir: Optional[str] = None,
    config_path: Optional[str] = None
) -> List[str]:
    """
    Run preprocessing on all subjects in a directory.

    Args:
        data_dir: Directory containing raw data. If None, defaults to
                  ``<project_root>/data/raw``.
        output_dir: Directory to save processed data. If None, defaults to
                    ``<project_root>/data/processed``.
        config_path: Path to config file. If None, defaults to
                     ``<project_root>/code/config.yaml``.

    Returns:
        List of output file paths.
    """
    project_root = get_project_root()
    if data_dir is None:
        data_dir = str(project_root / 'data' / 'raw')
    if output_dir is None:
        output_dir = str(project_root / 'data' / 'processed')
    if config_path is None:
        config_path = str(project_root / 'code' / 'config.yaml')

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    data_path = Path(data_dir)
    output_path = Path(output_dir)
    ensure_directory(output_path)

    output_files = []

    # Iterate over subject directories
    for subject_dir in sorted(data_path.iterdir()):
        if not subject_dir.is_dir() or not subject_dir.name.startswith('sub-'):
            continue
        subject_id = subject_dir.name
        logger.info(f"Processing subject {subject_id}")
        try:
            epochs = preprocess_subject(subject_id, config)
            output_files.append(str(output_path / f"{subject_id}_epo_raw.fif"))
        except Exception as e:
            logger.error(f"Failed to process {subject_id}: {e}")

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
