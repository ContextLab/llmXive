import mne
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from logger import get_logger
from config import get_config, get_paths

logger = get_logger(__name__)

class EpochingError(Exception):
    """Custom exception for epoching failures."""
    pass

def load_raw(path: str) -> mne.io.Raw:
    """
    Load raw EEG data from a file path.
    
    Args:
        path: Path to the raw data file (BIDS format preferred).
        
    Returns:
        mne.io.Raw object.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        RuntimeError: If loading fails.
    """
    logger.info(f"Loading raw data from: {path}")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Raw data file not found: {path}")
    
    try:
        # Attempt to load as FIF first, fallback to generic loading
        if path.endswith('.fif'):
            raw = mne.io.read_raw_fif(path, preload=True)
        elif path.endswith('.edf'):
            raw = mne.io.read_raw_edf(path, preload=True)
        else:
            # Try generic loader or raise if unsupported
            raw = mne.io.read_raw_brainvision(path, preload=True) if 'eeg' in path.lower() else mne.io.read_raw_bids(path, preload=True)
        
        logger.info(f"Loaded raw data: {raw.info['nchan']} channels, {raw.info['sfreq']} Hz")
        return raw
    except Exception as e:
        logger.error(f"Failed to load raw data: {e}")
        raise RuntimeError(f"Failed to load raw data: {e}")

def filter_data(raw: mne.io.Raw, lowcut: float = 1.0, highcut: float = 40.0, notch_freq: float = 50.0) -> mne.io.Raw:
    """
    Apply bandpass and notch filters to the raw data.
    
    Args:
        raw: Raw MNE object.
        lowcut: Low cutoff frequency for bandpass.
        highcut: High cutoff frequency for bandpass.
        notch_freq: Frequency for notch filter (50 or 60 Hz).
        
    Returns:
        Filtered mne.io.Raw object.
    """
    logger.info(f"Applying bandpass filter: {lowcut}-{highcut} Hz and notch filter: {notch_freq} Hz")
    raw_filtered = raw.copy()
    
    # Notch filter
    raw_filtered.notch_filter(notch_freq)
    
    # Bandpass filter
    raw_filtered.filter(lowcut, highcut)
    
    logger.info("Filtering complete")
    return raw_filtered

def run_ica(raw: mne.io.Raw, n_components: int = 20) -> mne.preprocessing.ICA:
    """
    Run ICA for artifact removal.
    
    Args:
        raw: Filtered raw MNE object.
        n_components: Number of ICA components to compute.
        
    Returns:
        Fitted ICA object.
    """
    logger.info(f"Running ICA with {n_components} components")
    ica = mne.preprocessing.ICA(n_components=n_components, random_state=42)
    ica.fit(raw)
    logger.info("ICA fitting complete")
    return ica

def find_and_remove_artifacts(ica: mne.preprocessing.ICA, raw: mne.io.Raw, 
                              eog_ch: Optional[str] = None, ecg_ch: Optional[str] = None) -> List[int]:
    """
    Find and identify bad components using EOG and ECG.
    
    Args:
        ica: Fitted ICA object.
        raw: Raw MNE object.
        eog_ch: Name of EOG channel.
        ecg_ch: Name of ECG channel.
        
    Returns:
        List of indices of bad components.
    """
    logger.info("Identifying bad components")
    bad_components = []
    
    # Find EOG artifacts
    if eog_ch:
        try:
            eog_inds, scores = ica.find_bads_eog(raw, ch_name=eog_ch)
            bad_components.extend(eog_inds)
            logger.info(f"Found {len(eog_inds)} EOG artifacts")
        except Exception as e:
            logger.warning(f"EOG artifact detection failed: {e}")
    
    # Find ECG artifacts
    if ecg_ch:
        try:
            ecg_inds, scores = ica.find_bads_ecg(raw, ch_name=ecg_ch)
            bad_components.extend(ecg_inds)
            logger.info(f"Found {len(ecg_inds)} ECG artifacts")
        except Exception as e:
            logger.warning(f"ECG artifact detection failed: {e}")
    
    # Unique sorted list
    bad_components = sorted(list(set(bad_components)))
    logger.info(f"Total bad components identified: {len(bad_components)}")
    return bad_components

def apply_ica_cleaning(raw: mne.io.Raw, ica: mne.preprocessing.ICA, bad_components: List[int]) -> mne.io.Raw:
    """
    Apply ICA cleaning by removing bad components.
    
    Args:
        raw: Raw MNE object.
        ica: Fitted ICA object.
        bad_components: List of component indices to remove.
        
    Returns:
        Cleaned raw MNE object.
    """
    if not bad_components:
        logger.info("No bad components to remove")
        return raw
    
    logger.info(f"Applying ICA cleaning, removing {len(bad_components)} components")
    ica.exclude = bad_components
    raw_clean = ica.apply(raw)
    logger.info("ICA cleaning complete")
    return raw_clean

def generate_manual_review_log(raw: mne.io.Raw, bad_components: List[int], log_path: str) -> None:
    """
    Generate a log file for manual review of rejected components.
    
    Args:
        raw: Raw MNE object.
        bad_components: List of rejected component indices.
        log_path: Path to save the log file.
    """
    logger.info(f"Generating manual review log at: {log_path}")
    with open(log_path, 'w') as f:
        f.write("Manual Review Log for ICA Components\n")
        f.write("=" * 40 + "\n\n")
        f.write(f"Total components rejected: {len(bad_components)}\n")
        f.write(f"Rejected component indices: {bad_components}\n\n")
        f.write("Recommendation: Inspect these components visually using mne.viz.plot_ica_components()\n")
        f.write("to confirm they represent artifacts before finalizing the cleaning.\n")
    logger.info("Manual review log generated")

def handle_missing_electrodes(raw: mne.io.Raw, metadata_path: str) -> List[str]:
    """
    Identify and skip electrodes with missing data (NaN or constant).
    Updates metadata.json with the list of skipped electrodes.
    
    Args:
        raw: Raw MNE object (can be pre- or post-filtering).
        metadata_path: Path to the metadata.json file.
        
    Returns:
        List of skipped electrode names.
    """
    logger.info("Checking for missing electrode data...")
    skipped_electrodes = []
    
    # Ensure metadata file exists
    metadata_dir = Path(metadata_path).parent
    metadata_dir.mkdir(parents=True, exist_ok=True)
    
    # Load existing metadata or initialize
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
        except (json.JSONDecodeError, IOError):
            metadata = {'skipped_electrodes': [], 'assumptions': {}, 'data_source_url': None, 'fetch_method': None}
    else:
        metadata = {'skipped_electrodes': [], 'assumptions': {}, 'data_source_url': None, 'fetch_method': None}
    
    # Check each channel
    ch_names = raw.info['ch_names']
    data = raw.get_data()
    sfreq = raw.info['sfreq']
    
    for i, ch_name in enumerate(ch_names):
        ch_data = data[i, :]
        
        # Check for all NaN
        if np.all(np.isnan(ch_data)):
            skipped_electrodes.append(ch_name)
            logger.warning(f"Electrode {ch_name} contains only NaN values. Skipping.")
            continue
        
        # Check for constant (zero variance) - indicates dead channel
        if np.std(ch_data) < 1e-10:
            skipped_electrodes.append(ch_name)
            logger.warning(f"Electrode {ch_name} has near-zero variance (dead channel). Skipping.")
            continue
        
        # Check for excessive NaN ratio (e.g., > 50% missing)
        nan_ratio = np.sum(np.isnan(ch_data)) / len(ch_data)
        if nan_ratio > 0.5:
            skipped_electrodes.append(ch_name)
            logger.warning(f"Electrode {ch_name} has {nan_ratio:.2%} missing values. Skipping.")
            continue
    
    # Update metadata
    if skipped_electrodes:
        existing_skipped = set(metadata.get('skipped_electrodes', []))
        new_skipped = set(skipped_electrodes)
        combined_skipped = list(existing_skipped | new_skipped)
        metadata['skipped_electrodes'] = combined_skipped
        logger.info(f"Updated skipped electrodes list: {combined_skipped}")
    else:
        logger.info("No missing electrodes detected.")
    
    # Save updated metadata
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    # Drop bad channels from raw if any
    if skipped_electrodes:
        logger.info(f"Dropping {len(skipped_electrodes)} channels from raw data...")
        raw.drop_channels(skipped_electrodes)
        logger.info("Channel dropping complete.")
    
    return skipped_electrodes

def epoch_segmentation(raw: mne.io.Raw, events: np.ndarray, event_id: Dict[str, int], 
                       tmin: float = -1.0, tmax: float = 1.0, sfreq: float = 1000.0) -> mne.Epochs:
    """
    Segment data into epochs around events.
    
    Args:
        raw: Raw MNE object.
        events: Array of events (n_events, 3).
        event_id: Dictionary mapping event names to IDs.
        tmin: Start time relative to event (seconds).
        tmax: End time relative to event (seconds).
        sfreq: Sampling frequency.
        
    Returns:
        MNE Epochs object.
    """
    logger.info(f"Segmenting data into epochs: {tmin}s to {tmax}s")
    try:
        epochs = mne.Epochs(raw, events, event_id, tmin, tmax, baseline=None, preload=True)
        logger.info(f"Created {len(epochs)} epochs")
        return epochs
    except Exception as e:
        logger.error(f"Epoching failed: {e}")
        raise EpochingError(f"Epoching failed: {e}")

def preprocess_pipeline_with_ica(raw: mne.io.Raw, metadata_path: str, 
                                 eog_ch: Optional[str] = None, ecg_ch: Optional[str] = None) -> mne.io.Raw:
    """
    Full preprocessing pipeline: Filter -> ICA -> Clean -> Handle Missing Electrodes.
    
    Args:
        raw: Raw MNE object.
        metadata_path: Path to metadata.json.
        eog_ch: EOG channel name.
        ecg_ch: ECG channel name.
        
    Returns:
        Preprocessed raw MNE object.
    """
    # 1. Filter
    raw = filter_data(raw)
    
    # 2. Handle missing electrodes BEFORE ICA to avoid fitting on bad channels
    handle_missing_electrodes(raw, metadata_path)
    
    # 3. ICA
    ica = run_ica(raw)
    
    # 4. Find artifacts
    bad_components = find_and_remove_artifacts(ica, raw, eog_ch, ecg_ch)
    
    # 5. Manual review log
    log_path = str(Path(metadata_path).parent / "ica_review.log")
    generate_manual_review_log(raw, bad_components, log_path)
    
    # 6. Apply cleaning
    raw = apply_ica_cleaning(raw, ica, bad_components)
    
    return raw

def main():
    """Main entry point for preprocessing."""
    config = get_config()
    paths = get_paths()
    metadata_path = paths['output_path'] / 'metadata.json'
    
    # Example usage (to be replaced by actual pipeline integration)
    logger.info("Preprocessing module initialized.")
    logger.info(f"Metadata path: {metadata_path}")

if __name__ == "__main__":
    main()
