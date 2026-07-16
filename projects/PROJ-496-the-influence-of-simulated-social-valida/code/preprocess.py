import argparse
import logging
import os
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any

import numpy as np
import mne
from mne.preprocessing import ICA
from config import set_seeds, get_env_var, ensure_dirs
from logger import get_logger

logger = get_logger(__name__)

def setup_argparse() -> argparse.ArgumentParser:
    """Set up command-line argument parser for preprocessing."""
    parser = argparse.ArgumentParser(description="Preprocess EEG data and extract P300 features.")
    parser.add_argument("--data_dir", type=str, required=True, help="Path to raw EEG data directory")
    parser.add_argument("--output_dir", type=str, required=True, help="Path to output processed data directory")
    parser.add_argument("--low_cutoff", type=float, default=0.1, help="Low cutoff for band-pass filter (Hz)")
    parser.add_argument("--high_cutoff", type=float, default=40.0, help="High cutoff for band-pass filter (Hz)")
    parser.add_argument("--rejection_threshold", type=float, default=100.0, help="Rejection threshold in microvolts")
    parser.add_argument("--baseline_start", type=float, default=-0.2, help="Baseline start time (s)")
    parser.add_argument("--baseline_end", type=float, default=0.0, help="Baseline end time (s)")
    parser.add_argument("--tmin", type=float, default=-0.2, help="Epoch start time relative to stimulus (s)")
    parser.add_argument("--tmax", type=float, default=0.8, help="Epoch end time relative to stimulus (s)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    return parser

def load_raw_eeg(data_dir: Path) -> mne.io.BaseRaw:
    """Load raw EEG data from directory. Supports .edf, .bdf, .set, etc."""
    raw_files = list(data_dir.glob("*.edf")) + list(data_dir.glob("*.bdf")) + list(data_dir.glob("*.set"))
    if not raw_files:
        raise FileNotFoundError(f"No EEG files found in {data_dir}")
    
    raw_file = raw_files[0]
    logger.info(f"Loading raw EEG file: {raw_file}")
    
    # Determine file type based on extension
    suffix = raw_file.suffix.lower()
    if suffix == '.edf':
        raw = mne.io.read_raw_edf(raw_file, preload=True, verbose=False)
    elif suffix == '.bdf':
        raw = mne.io.read_raw_bdf(raw_file, preload=True, verbose=False)
    elif suffix == '.set':
        raw = mne.io.read_raw_eeglab(raw_file, preload=True, verbose=False)
    else:
        # Try generic reader
        raw = mne.io.read_raw(raw_file, preload=True, verbose=False)
    
    # Standardize channel names to uppercase
    raw.rename_channels({ch: ch.upper() for ch in raw.ch_names}, copy=False)
    
    # Set montage if not present (standard 10-20 system)
    if raw.get_montage() is None:
        try:
            montage = mne.channels.make_standard_montage('standard_1005')
            raw.set_montage(montage, match_case=False, match_alias=True, on_missing='ignore')
        except Exception as e:
            logger.warning(f"Could not set montage: {e}")
    
    return raw

def apply_bandpass_filter(raw: mne.io.BaseRaw, low_cutoff: float, high_cutoff: float) -> mne.io.BaseRaw:
    """Apply band-pass filter to raw EEG data."""
    logger.info(f"Applying band-pass filter: {low_cutoff}Hz - {high_cutoff}Hz")
    raw_filtered = raw.copy()
    raw_filtered.filter(low_cutoff, high_cutoff, method='fir', fir_design='firwin', verbose=False)
    return raw_filtered

def average_reference(raw: mne.io.BaseRaw) -> mne.io.BaseRaw:
    """Apply average reference to EEG data."""
    logger.info("Applying average reference")
    raw_ref = raw.copy()
    
    # Exclude non-EEG channels from average reference calculation
    eeg_picks = mne.pick_types(raw_ref.info, eeg=True, exclude='bads')
    if len(eeg_picks) == 0:
        logger.warning("No EEG channels found for average reference. Skipping.")
        return raw_ref
    
    raw_ref.set_eeg_reference(ref_channels='average', projection=False)
    return raw_ref

def run_ica_artifact_removal(raw: mme.io.BaseRaw, n_components: float = 0.99, 
                             method: str = 'fastica', random_state: int = 42) -> mne.io.BaseRaw:
    """
    Run ICA to remove ocular artifacts (blinks, saccades).
    
    This function:
    1. Fits ICA to the EEG data
    2. Identifies components correlated with EOG channels (or EOG-like signals)
    3. Removes those components
    4. Reconstructs the clean signal
    
    Args:
        raw: Preprocessed and averaged-referenced raw data
        n_components: Number of components to keep (float 0-1 for explained variance, or int for count)
        method: ICA algorithm ('fastica', 'picard', 'infomax')
        random_state: Random seed for reproducibility
        
    Returns:
        Raw data with ocular artifacts removed
    """
    logger.info("Running ICA-based ocular artifact removal")
    
    # Create a copy to avoid modifying original
    raw_ica = raw.copy()
    
    # Pick EEG channels for ICA
    eeg_picks = mne.pick_types(raw_ica.info, eeg=True, exclude='bads')
    if len(eeg_picks) < 10:
        logger.warning("Too few EEG channels for ICA. Skipping ICA.")
        return raw_ica
    
    # Find EOG channels (look for channels containing 'EOG', 'EOG', 'HEOG', 'VEOG' in name)
    eog_picks = mne.pick_types(raw_ica.info, eog=True, exclude='bads')
    
    # If no dedicated EOG channels, try to find them by name pattern
    if len(eog_picks) == 0:
        eog_candidates = [ch for ch in raw_ica.ch_names if any(k in ch.upper() for k in ['EOG', 'HEOG', 'VEOG'])]
        if eog_candidates:
            eog_picks = [raw_ica.ch_names.index(ch) for ch in eog_candidates]
            logger.info(f"Found EOG channels by name: {[raw_ica.ch_names[i] for i in eog_picks]}")
        else:
            # Fallback: use a frontal electrode as proxy for EOG (e.g., FP1, FP2, FpZ)
            eog_proxy = [ch for ch in ['FP1', 'FP2', 'FPZ', 'F7', 'F8'] if ch in raw_ica.ch_names]
            if eog_proxy:
                eog_picks = [raw_ica.ch_names.index(ch) for ch in eog_proxy]
                logger.info(f"Using proxy EOG channels: {[raw_ica.ch_names[i] for i in eog_picks]}")
            else:
                logger.warning("No EOG channels or proxies found. ICA will use all channels for component detection.")
                eog_picks = None
    
    # Fit ICA
    logger.info(f"Fitting ICA with method '{method}' and n_components={n_components}")
    ica = ICA(n_components=n_components, method=method, random_state=random_state, verbose=False)
    
    # Exclude bad channels from ICA fitting
    bads = raw_ica.info['bads']
    ica.fit(raw_ica, exclude=bads)
    
    logger.info(f"ICA fitted: {len(ica.pca_explained_variance_)} components found")
    
    # Find components to exclude based on correlation with EOG
    if eog_picks:
        logger.info("Finding EOG-related components...")
        eog_indices = ica.find_bads_eog(raw_ica, ch_name=eog_picks if isinstance(eog_picks, list) else None, threshold=3.0)
        logger.info(f"Found {len(eog_indices)} EOG-related components: {eog_indices}")
    else:
        # If no EOG channels, we can't automatically find ocular components
        # In this case, we skip automatic removal but log the warning
        logger.warning("No EOG channels available for automatic component detection. Skipping component removal.")
        eog_indices = []
    
    # Apply ICA to remove identified components
    if eog_indices:
        ica.exclude = eog_indices
        logger.info(f"Applying ICA to remove components: {ica.exclude}")
        ica.apply(raw_ica)
    else:
        logger.info("No components to remove. Returning data as-is.")
    
    return raw_ica

def epoch_data(raw: mne.io.BaseRaw, events: np.ndarray, event_id: Dict[str, int], 
               tmin: float, tmax: float, baseline: Optional[tuple] = None) -> mne.Epochs:
    """Create epochs from raw data around stimulus events."""
    logger.info(f"Creating epochs from {len(events)} events")
    
    epochs = mne.Epochs(raw, events, event_id, tmin, tmax, baseline=baseline, 
                       preload=True, verbose=False)
    return epochs

def reject_epochs(epochs: mne.Epochs, rejection_threshold: float) -> mne.Epochs:
    """Reject epochs based on peak-to-peak amplitude threshold."""
    logger.info(f"Rejecting epochs with amplitude > {rejection_threshold} µV")
    
    # Convert threshold from microvolts to volts (MNE uses Volts)
    rejection_dict = dict(eeg=rejection_threshold * 1e-6)
    
    # Get number of epochs before rejection
    n_before = len(epochs)
    
    # Apply rejection
    epochs_clean = epochs.copy().drop_bad(rejection=rejection_dict)
    n_after = len(epochs_clean)
    
    retention_rate = n_after / n_before if n_before > 0 else 0
    logger.info(f"Epoch retention: {n_after}/{n_before} ({retention_rate:.1%})")
    
    return epochs_clean

def extract_p300_features(epochs: mne.Epochs, condition: str) -> List[Dict[str, Any]]:
    """Extract P300 amplitude and latency features from epochs."""
    logger.info(f"Extracting P300 features for condition: {condition}")
    
    # Average reference is already applied to epochs
    # Find P300 peak in time window 250-500ms at Pz and CPz
    p300_results = []
    
    # Define electrodes of interest
    eeg_picks = mne.pick_types(epochs.info, eeg=True)
    ch_names = [epochs.ch_names[i] for i in eeg_picks]
    
    target_channels = ['PZ', 'CPZ']
    available_targets = [ch for ch in target_channels if ch in ch_names]
    
    if not available_targets:
        # Fallback to closest available channel if Pz/CPz not found
        available_targets = [ch for ch in ch_names if 'P' in ch or 'C' in ch]
        if not available_targets:
            logger.warning("No suitable channels found for P300 extraction")
            return p300_results
    
    # Time window for P300 (250-500ms)
    time_window = (0.25, 0.50)
    
    for epoch_idx in range(len(epochs)):
        epoch_data = epochs.get_data()[epoch_idx]  # Shape: (n_channels, n_times)
        times = epochs.times
        
        # Find time indices for P300 window
        time_indices = np.where((times >= time_window[0]) & (times <= time_window[1]))[0]
        if len(time_indices) == 0:
            continue
        
        for ch_name in available_targets:
            ch_idx = epochs.ch_names.index(ch_name)
            if ch_idx >= len(epoch_data):
                continue
            
            channel_data = epoch_data[ch_idx, time_indices]
            time_point = times[time_indices[np.argmax(channel_data)]]
            amplitude = np.max(channel_data)
            
            p300_results.append({
                'subject_id': epochs.metadata['subject_id'][epoch_idx] if 'subject_id' in epochs.metadata.columns else f'sub_{epoch_idx:03d}',
                'condition': condition,
                'channel': ch_name,
                'p300_amplitude': float(amplitude * 1e6),  # Convert to microvolts
                'p300_latency': float(time_point),
                'epoch_index': epoch_idx
            })
    
    return p300_results

def run_preprocess_phase(data_dir: Path, output_dir: Path, low_cutoff: float, high_cutoff: float,
                         rejection_threshold: float, baseline: tuple, tmin: float, tmax: float,
                         seed: int) -> None:
    """Run the full preprocessing pipeline."""
    logger.info(f"Starting preprocessing phase: {data_dir} -> {output_dir}")
    
    # Set random seeds for reproducibility
    set_seeds(seed)
    
    # Ensure output directory exists
    ensure_dirs(output_dir)
    
    # Load raw data
    raw = load_raw_eeg(data_dir)
    
    # Apply band-pass filter
    raw_filtered = apply_bandpass_filter(raw, low_cutoff, high_cutoff)
    
    # Apply average reference
    raw_ref = average_reference(raw_filtered)
    
    # Run ICA for ocular artifact removal
    raw_clean = run_ica_artifact_removal(raw_ref, random_state=seed)
    
    # Create events (dummy events for demonstration - in real use, events would come from annotations)
    # For now, create synthetic events at regular intervals
    n_epochs = 20  # Number of epochs to create
    event_times = np.linspace(1.0, len(raw_clean.times) / raw_clean.info['sfreq'] - 2.0, n_epochs)
    events = np.column_stack([
        np.arange(n_epochs) * int(raw_clean.info['sfreq'] * 2.0),  # Sample positions (approx)
        np.zeros(n_epochs, dtype=int),  # Previous event (0)
        np.ones(n_epochs, dtype=int)    # Event ID (1)
    ])
    
    event_id = {'stimulus': 1}
    
    # Epoch data
    epochs = epoch_data(raw_clean, events, event_id, tmin, tmax, baseline=baseline)
    
    # Reject bad epochs
    epochs_clean = reject_epochs(epochs, rejection_threshold)
    
    # Extract P300 features
    p300_features = extract_p300_features(epochs_clean, 'stimulus')
    
    # Save results
    output_file = output_dir / 'p300_measures.csv'
    import pandas as pd
    df = pd.DataFrame(p300_features)
    df.to_csv(output_file, index=False)
    logger.info(f"Saved P300 measures to {output_file}")
    
    # Save preprocessed raw data
    raw_output_path = output_dir / 'preprocessed_raw.fif'
    raw_clean.save(raw_output_path, overwrite=True)
    logger.info(f"Saved preprocessed raw data to {raw_output_path}")

def main():
    """Main entry point for preprocessing."""
    parser = setup_argparse()
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    data_dir = Path(args.data_dir)
    output_dir = Path(args.output_dir)
    
    if not data_dir.exists():
        logger.error(f"Data directory does not exist: {data_dir}")
        sys.exit(1)
    
    run_preprocess_phase(
        data_dir=data_dir,
        output_dir=output_dir,
        low_cutoff=args.low_cutoff,
        high_cutoff=args.high_cutoff,
        rejection_threshold=args.rejection_threshold,
        baseline=(args.baseline_start, args.baseline_end),
        tmin=args.tmin,
        tmax=args.tmax,
        seed=args.seed
    )

if __name__ == "__main__":
    main()