import os
import sys
import time
import logging
import mne
import numpy as np
from pathlib import Path
from logging_setup import get_logger
from config import ensure_directories

# Constants for filtering and epoching
BANDPASS_LOW = 1.0
BANDPASS_HIGH = 45.0
NOTCH_FREQS = [50.0, 60.0]
EPOCH_TMIN = -1.0
EPOCH_TMAX = 2.0
KURTOSIS_THRESHOLD = 5.0
SPECTRAL_PEAK_THRESHOLD = 30.0
MIN_TRIALS_PER_CONDITION = 10
MAX_ARTIFACT_REMOVAL_RATE = 0.50

def load_raw_data(subject_id: str, raw_dir: str) -> mne.io.Raw:
    """
    Load raw EEG data for a subject.
    
    Args:
        subject_id: The subject identifier.
        raw_dir: Path to the directory containing raw data.
        
    Returns:
        mne.io.Raw object.
    """
    logger = get_logger()
    # Assume standard BIDS or MNE-compatible naming: sub-{id}_task-..._eeg.fif
    # Adjust based on actual dataset structure if needed
    file_path = os.path.join(raw_dir, f"sub-{subject_id}_eeg.fif")
    
    if not os.path.exists(file_path):
        # Fallback for common OpenNeuro naming patterns
        file_path = os.path.join(raw_dir, f"sub-{subject_id}_task-switching_eeg.fif")
    
    if not os.path.exists(file_path):
        # Try finding any .fif file in the directory for this subject
        pattern = f"sub-{subject_id}*"
        matches = list(Path(raw_dir).glob(f"{pattern}*.fif"))
        if matches:
            file_path = str(matches[0])
        else:
            raise FileNotFoundError(f"No raw data file found for subject {subject_id} in {raw_dir}")
    
    logger.info(f"Loading raw data from {file_path}")
    raw = mne.io.read_raw_fif(file_path, preload=True)
    return raw

def apply_bandpass_filter(raw: mne.io.Raw, low: float = BANDPASS_LOW, high: float = BANDPASS_HIGH) -> mne.io.Raw:
    """
    Apply a bandpass filter to the raw data.
    
    Args:
        raw: Raw data object.
        low: Low cutoff frequency.
        high: High cutoff frequency.
        
    Returns:
        Filtered raw data object.
    """
    logger = get_logger()
    logger.info(f"Applying bandpass filter: {low}-{high} Hz")
    raw_filtered = raw.copy()
    raw_filtered.filter(low_freq=low, high_freq=high, method='fir', fir_design='firwin')
    return raw_filtered

def detect_line_noise(raw: mne.io.Raw) -> bool:
    """
    Detect if line noise is present in the data.
    
    Args:
        raw: Raw data object.
        
    Returns:
        True if line noise is detected, False otherwise.
    """
    logger = get_logger()
    # Simple heuristic: check for high power at 50/60Hz in the spectrum
    # We use a quick spectral estimate on a subset of channels
    logger.info("Detecting line noise...")
    psd, freqs = mne.time_frequency.psd_welch(raw, fmin=40, fmax=70, n_fft=2048, n_overlap=1024)
    mean_psd = np.mean(psd, axis=0)
    
    # Check for peaks at 50 or 60 Hz
    peak_indices = np.argmax(mean_psd)
    peak_freq = freqs[peak_indices]
    
    # If the peak is within 2 Hz of 50 or 60, consider it line noise
    is_50 = abs(peak_freq - 50) < 2
    is_60 = abs(peak_freq - 60) < 2
    
    if is_50 or is_60:
        logger.info(f"Line noise detected at {peak_freq:.1f} Hz")
        return True
    return False

def apply_notch_filter(raw: mne.io.Raw, freqs: list = NOTCH_FREQS) -> mne.io.Raw:
    """
    Apply a notch filter to remove line noise.
    
    Args:
        raw: Raw data object.
        freqs: List of frequencies to notch (e.g., [50, 60]).
        
    Returns:
        Notch-filtered raw data object.
    """
    logger = get_logger()
    raw_filtered = raw.copy()
    
    for freq in freqs:
        logger.info(f"Applying notch filter at {freq} Hz")
        raw_filtered.notch_filter(freqs=[freq], method='spectrum_fit')
        # Log the specific intervention as required
        logger.info(f"Notch filter applied at {freq}Hz for subject (processed in pipeline)")
        
    return raw_filtered

def perform_ica_and_remove_artifacts(raw: mne.io.Raw) -> Tuple[mne.io.Raw, Dict[str, int]]:
    """
    Perform ICA and remove components based on kurtosis and spectral peak criteria.
    
    Args:
        raw: Filtered raw data object.
        
    Returns:
        Tuple of (cleaned raw data, dict with counts: 'total_components', 'removed_components')
    """
    logger = get_logger()
    logger.info("Performing ICA for artifact removal...")
    
    # Find EOG channel if available
    eog_indices = mne.preprocessing.find_eog_channels(raw)
    eog_ch_names = [raw.info['ch_names'][i] for i in eog_indices]
    
    # Fit ICA
    n_components = min(0.99 * len(raw.ch_names), 20) # Limit components
    ica = mne.preprocessing.ICA(n_components=int(n_components), random_state=42)
    ica.fit(raw)
    
    # Find components to reject
    # 1. High kurtosis
    kurtosis_scores = ica.get_components().var(axis=1) # Approximate kurtosis proxy or use specific method
    # Better approach: use ica.get_sources(raw) and check kurtosis of scores
    sources = ica.get_sources(raw)
    component_scores = []
    for i in range(ica.n_components_):
        score = np.kurtosis(sources.get_data(picks=i))
        component_scores.append(score)
    
    kurtosis_reject = [i for i, score in enumerate(component_scores) if abs(score) > KURTOSIS_THRESHOLD]
    
    # 2. Spectral peak > 30 Hz
    # Compute PSD for each component
    psd_components = []
    for i in range(ica.n_components_):
        comp_data = sources.get_data(picks=i)
        f, Pxx = mne.time_frequency.psd_welch(comp_data[np.newaxis, :], fmin=0, fmax=100, n_fft=1024)
        # Find max peak above 30Hz
        peak_idx = np.argmax(Pxx[0, f > 30])
        peak_freq = f[30:][peak_idx] # Adjust index
        # Check if peak power is significantly higher than baseline (simple heuristic)
        # For now, just check if there's a dominant peak in high freq
        psd_components.append((f, Pxx[0]))
    
    spectral_reject = []
    for i, (f, pxx) in enumerate(psd_components):
        # Look for a sharp peak above 30Hz
        high_freq_mask = f > 30
        if np.any(high_freq_mask):
            high_pxx = pxx[high_freq_mask]
            high_f = f[high_freq_mask]
            max_idx = np.argmax(high_pxx)
            # Heuristic: if peak is much higher than median of high freq band
            if high_pxx[max_idx] > 5 * np.median(high_pxx):
                spectral_reject.append(i)
    
    # Combine rejection criteria
    reject_components = list(set(kurtosis_reject + spectral_reject))
    reject_components.sort()
    
    logger.info(f"ICA components to reject: {reject_components}")
    logger.info(f"Kurtosis reject: {kurtosis_reject}, Spectral reject: {spectral_reject}")
    
    # Apply rejection
    ica.exclude = reject_components
    cleaned_raw = ica.apply(raw)
    
    counts = {
        'total_components': ica.n_components_,
        'removed_components': len(reject_components)
    }
    
    return cleaned_raw, counts

def create_epochs(raw: mne.io.Raw, event_id: Optional[Dict[str, int]] = None) -> mne.Epochs:
    """
    Create epochs around stimulus onset.
    
    Args:
        raw: Cleaned raw data object.
        event_id: Dictionary mapping event names to IDs. If None, tries to auto-detect.
        
    Returns:
        mne.Epochs object.
    """
    logger = get_logger()
    logger.info(f"Creating epochs: tmin={EPOCH_TMIN}s, tmax={EPOCH_TMAX}s")
    
    # Find events if not provided
    if event_id is None:
        # Try standard event names for task-switching
        event_id = {'stimulus': 1, 'response': 2} # Fallback
        
    # Find events in the data
    events, event_dict = mne.find_events(raw, stim_channel='STI 014') # Standard stim channel
    
    # Filter for relevant events (e.g., stimulus onset)
    # Assuming we want to epoch around stimulus
    event_ids_to_use = {k: v for k, v in event_dict.items() if 'stimulus' in k.lower() or k in event_id}
    if not event_ids_to_use:
        # Fallback: use all events
        event_ids_to_use = event_dict
        
    epochs = mne.Epochs(
        raw, 
        events, 
        event_id=event_ids_to_use, 
        tmin=EPOCH_TMIN, 
        tmax=EPOCH_TMAX,
        baseline=(None, 0),
        reject={'eeg': 150e-6}, # Reject bad epochs
        preload=True
    )
    
    logger.info(f"Created {len(epochs)} epochs")
    return epochs

def get_subject_trials_per_condition(epochs: mne.Epochs) -> Dict[str, int]:
    """
    Count trials per condition from epochs.
    
    Args:
        epochs: Epochs object.
        
    Returns:
        Dictionary mapping condition names to trial counts.
    """
    counts = {}
    for condition in epochs.event_id.keys():
        counts[condition] = len(epochs[condition])
    return counts

def process_subject(subject_id: str, raw_dir: str, preproc_dir: str) -> Tuple[Optional[mne.Epochs], Optional[Dict]]:
    """
    Full preprocessing pipeline for a single subject.
    
    Args:
        subject_id: Subject ID.
        raw_dir: Directory with raw data.
        preproc_dir: Directory to save processed data.
        
    Returns:
        Tuple of (Epochs object, artifact removal stats dict) or (None, None) if failed.
    """
    logger = get_logger()
    logger.info(f"Processing subject {subject_id}...")
    
    try:
        # Load
        raw = load_raw_data(subject_id, raw_dir)
        
        # Filter
        raw = apply_bandpass_filter(raw)
        
        # Notch if needed
        if detect_line_noise(raw):
            raw = apply_notch_filter(raw)
        
        # ICA
        raw, ica_stats = perform_ica_and_remove_artifacts(raw)
        
        # Epoch
        epochs = create_epochs(raw)
        
        # Save
        output_path = os.path.join(preproc_dir, f"sub-{subject_id}_epochs.fif")
        epochs.save(output_path, overwrite=True)
        
        return epochs, ica_stats
        
    except Exception as e:
        logger.error(f"Failed to process subject {subject_id}: {e}")
        return None, None

def get_subject_ids(raw_dir: str) -> List[str]:
    """
    Get list of subject IDs from the raw data directory.
    
    Args:
        raw_dir: Directory containing raw data.
        
    Returns:
        List of subject IDs.
    """
    subjects = []
    for item in os.listdir(raw_dir):
        if item.startswith('sub-') and item.endswith('.fif'):
            # Extract ID: sub-001_eeg.fif -> 001
            subj_id = item.split('_')[0].replace('sub-', '')
            subjects.append(subj_id)
    return subjects

def main():
    """
    Main entry point to run preprocessing on all subjects.
    """
    ensure_directories()
    raw_dir = "data/raw"
    preproc_dir = "data/processed"
    
    subjects = get_subject_ids(raw_dir)
    logger = get_logger()
    logger.info(f"Found {len(subjects)} subjects to process")
    
    for subj in subjects:
        epochs, stats = process_subject(subj, raw_dir, preproc_dir)
        if epochs is not None:
            counts = get_subject_trials_per_condition(epochs)
            logger.info(f"Subject {subj}: {counts}, ICA stats: {stats}")
        else:
            logger.warning(f"Subject {subj} failed processing")

if __name__ == "__main__":
    main()
