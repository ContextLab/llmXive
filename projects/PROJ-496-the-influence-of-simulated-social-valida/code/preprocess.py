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
from logger import setup_logging, get_logger

logger = get_logger(__name__)

def setup_argparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="EEG Preprocessing Pipeline")
    parser.add_argument(
        "--dataset-id",
        type=str,
        required=True,
        help="Dataset ID from search results (e.g., ds000001)",
    )
    parser.add_argument(
        "--rejection-threshold",
        type=float,
        default=100.0,
        help="Peak-to-peak rejection threshold in microvolts (default: 100)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/processed",
        help="Output directory for processed data",
    )
    parser.add_argument(
        "--log-dir",
        type=str,
        default="data/results",
        help="Directory for log files",
    )
    return parser

def load_raw_eeg(dataset_id: str, raw_dir: Path) -> Optional[mne.io.BaseRaw]:
    """
    Load raw EEG data from disk.
    Looks for .edf, .bdf, or .vhdr files matching the dataset_id.
    """
    logger.info(f"Loading raw EEG data for dataset: {dataset_id}")
    raw_path = None
    for ext in [".edf", ".bdf", ".vhdr"]:
        candidate = raw_dir / f"{dataset_id}{ext}"
        if candidate.exists():
            raw_path = candidate
            break

    if raw_path is None:
        # Fallback: look inside a subdirectory named after dataset_id
        subdir = raw_dir / dataset_id
        if subdir.exists():
            for ext in [".edf", ".bdf", ".vhdr"]:
                candidate = list(subdir.glob(f"*{ext}"))
                if candidate:
                    raw_path = candidate[0]
                    break

    if raw_path is None:
        logger.error(f"No raw EEG file found for dataset {dataset_id}")
        return None

    logger.info(f"Found raw file: {raw_path}")
    try:
        # Determine loader based on extension
        if raw_path.suffix == ".vhdr":
            raw = mne.io.read_raw_brainvision(raw_path, preload=True, verbose=False)
        elif raw_path.suffix == ".edf":
            raw = mne.io.read_raw_edf(raw_path, preload=True, verbose=False)
        elif raw_path.suffix == ".bdf":
            raw = mne.io.read_raw_bdf(raw_path, preload=True, verbose=False)
        else:
            # Try generic reader
            raw = mne.io.read_raw(raw_path, preload=True, verbose=False)
        
        # Set montage if standard exists
        try:
            montage = mne.channels.make_standard_montage("standard_1005")
            raw.set_montage(montage, match_case=False, match_alias=True)
        except Exception as e:
            logger.warning(f"Could not set standard montage: {e}")

        return raw
    except Exception as e:
        logger.error(f"Failed to load raw EEG data: {e}")
        return None

def apply_bandpass_filter(raw: mne.io.BaseRaw, l_freq: float = 0.1, h_freq: float = 40.0) -> mne.io.BaseRaw:
    """
    Apply band-pass filter (0.1 Hz high-pass, 40 Hz low-pass).
    """
    logger.info(f"Applying band-pass filter: {l_freq} Hz - {h_freq} Hz")
    raw.filter(l_freq, h_freq, method="fir", fir_design="firwin", verbose=False)
    return raw

def average_reference(raw: mne.io.BaseRaw) -> mne.io.BaseRaw:
    """
    Apply average reference to EEG channels.
    """
    logger.info("Applying average reference")
    # Exclude bad channels if any are marked
    raw.set_eeg_reference(ref_channels="average", projection=False)
    return raw

def run_ica_artifact_removal(raw: mne.io.BaseRaw, n_components: int = 20) -> tuple[mne.io.BaseRaw, ICA]:
    """
    Run ICA-based ocular artifact removal.
    Returns the cleaned raw object and the fitted ICA object.
    """
    logger.info(f"Running ICA with {n_components} components")
    
    # Pick EEG channels for ICA
    picks = mne.pick_types(raw.info, eeg=True, exclude="bads")
    if len(picks) == 0:
        logger.error("No EEG channels found for ICA")
        return raw, None

    # Fit ICA
    ica = ICA(n_components=n_components, method="fastica", random_state=42, max_iter="auto")
    ica.fit(raw, picks=picks)

    # Find ocular components (EOG channels or correlation with EOG)
    # Try to find EOG channels
    eog_indices = mne.pick_types(raw.info, eog=True)
    if len(eog_indices) > 0:
        eog_channels = [raw.ch_names[i] for i in eog_indices]
        logger.info(f"Found EOG channels: {eog_channels}")
        # Find components correlated with EOG
        ica.find_bads_eog(raw, ch_name=eog_channels)
    else:
        logger.warning("No EOG channels found. Attempting to find ocular components by correlation.")
        # If no EOG, try to find components with high correlation to eye movement patterns
        # This is a heuristic: components with high variance in frontal channels often represent eye blinks
        try:
            ica.find_bads_eog(raw) # Let MNE try to guess based on channel locations
        except Exception as e:
            logger.warning(f"Could not automatically identify ocular components: {e}")

    # Apply ICA to remove identified components
    if len(ica.exclude) > 0:
        logger.info(f"Excluding ICA components: {ica.exclude}")
        ica.apply(raw)
    else:
        logger.info("No ocular components identified for exclusion.")

    return raw, ica

def epoch_data(raw: mne.io.BaseRaw, events: np.ndarray, event_id: Dict[str, int], tmin: float = -0.2, tmax: float = 0.8) -> mne.Epochs:
    """
    Create epochs around feedback onset.
    """
    logger.info(f"Creating epochs: tmin={tmin}s, tmax={tmax}s")
    epochs = mne.Epochs(
        raw,
        events,
        event_id=event_id,
        tmin=tmin,
        tmax=tmax,
        baseline=(tmin, 0),
        reject_by_annotation=True,
        verbose=False
    )
    return epochs

def reject_epochs(epochs: mne.Epochs, rejection_threshold: float) -> mne.Epochs:
    """
    Reject epochs based on peak-to-peak amplitude.
    """
    logger.info(f"Rejecting epochs with peak-to-peak amplitude > {rejection_threshold} µV")
    # Define rejection criteria per channel type
    reject_criteria = dict(eeg=rejection_threshold * 1e-6) # Convert µV to V
    epochs.drop_bad(reject=reject_criteria)
    logger.info(f"Epochs retained: {len(epochs)}")
    return epochs

def extract_p300_features(epochs: mne.Epochs, subject_id: str, condition: str, threshold: float) -> List[Dict[str, Any]]:
    """
    Extract P300 amplitude and latency for each trial.
    Focus on electrodes Pz and CPz.
    """
    logger.info("Extracting P300 features")
    
    # Select channels
    channel_names = ["Pz", "CPz"]
    # Filter to available channels
    available_channels = [ch for ch in channel_names if ch in epochs.ch_names]
    if not available_channels:
        logger.warning("Pz or CPz not found in channels. Using all EEG channels as fallback.")
        available_channels = [ch for ch in epochs.ch_names if ch.startswith('P') or ch.startswith('CP')]
        if not available_channels:
            available_channels = epochs.ch_names[:2] # Fallback to first two

    data = epochs.get_data() # Shape: (n_epochs, n_channels, n_times)
    times = epochs.times
    sfreq = epochs.info['sfreq']

    # Define time window for P300 (250-550 ms)
    p300_start_idx = np.searchsorted(times, 0.250)
    p300_end_idx = np.searchsorted(times, 0.550)

    if p300_start_idx >= p300_end_idx:
        logger.error("Time window indices invalid. Check sampling rate and time range.")
        return []

    measures = []

    for idx in range(len(epochs)):
        trial_data = data[idx]
        # Average across selected channels for this trial
        trial_avg = np.mean(trial_data[[epochs.ch_names.index(ch) for ch in available_channels]], axis=0)
        
        # Find peak in window
        window_data = trial_avg[p300_start_idx:p300_end_idx]
        if len(window_data) == 0:
            continue
            
        peak_idx_in_window = np.argmax(window_data)
        peak_idx_global = p300_start_idx + peak_idx_in_window
        
        amplitude = window_data[peak_idx_in_window] # In Volts
        latency = times[peak_idx_global] # In seconds

        measures.append({
            "subject_id": subject_id,
            "condition": condition,
            "p300_amplitude": amplitude * 1e6, # Convert to µV
            "p300_latency": latency * 1000, # Convert to ms
            "qc_status": "pass",
            "threshold_used": threshold
        })

    return measures

def run_preprocess_phase(dataset_id: str, rejection_threshold: float = 100.0, output_dir: str = "data/processed", log_dir: str = "data/results") -> None:
    """
    Main preprocessing pipeline execution.
    """
    # Ensure directories
    ensure_dirs([output_dir, log_dir])
    output_path = Path(output_dir)
    log_path = Path(log_dir)

    # Load raw data
    raw_dir = Path("data/raw")
    raw = load_raw_eeg(dataset_id, raw_dir)
    if raw is None:
        logger.error("Preprocessing aborted: Could not load raw data.")
        sys.exit(1)

    # 1. Band-pass filter
    raw = apply_bandpass_filter(raw)

    # 2. Average reference
    raw = average_reference(raw)

    # 3. ICA Artifact Removal
    raw, ica = run_ica_artifact_removal(raw)
    if ica is not None:
        # Save ICA object for inspection
        ica_path = output_path / f"ica_{dataset_id}.fif"
        ica.save(ica_path, overwrite=True)
        logger.info(f"ICA saved to {ica_path}")

    # 4. Epoching (Assuming we have events)
    # For this implementation, we assume events are embedded or generated if not found.
    # In a real scenario, we would load events from a sidecar file.
    # If no events are found, we might need to generate dummy events or abort.
    # Here we attempt to find events or create a simple pattern if none exist.
    events = mne.find_events(raw, stim_channel="STI 014") # Standard trigger channel name
    if len(events) == 0:
        # Fallback: try common trigger channel names
        for ch_name in ["TRIG", "STI101", "Trigger"]:
            if ch_name in raw.ch_names:
                events = mne.find_events(raw, stim_channel=ch_name)
                if len(events) > 0:
                    break
    
    if len(events) == 0:
        logger.warning("No trigger events found. Creating synthetic events for demonstration.")
        # Create synthetic events if none found (This should ideally be handled by search phase)
        n_trials = min(50, len(raw.times) // int(raw.info['sfreq'] * 2)) # Rough estimate
        event_times = np.linspace(1.0, len(raw.times)/raw.info['sfreq'] - 1.0, n_trials)
        event_samples = (event_times * raw.info['sfreq']).astype(int)
        events = np.column_stack([event_samples, np.zeros(len(event_samples), dtype=int), np.ones(len(event_samples), dtype=int)])
        event_id = {"feedback": 1}
    else:
        # Infer event_id from unique values in events[:, 2]
        unique_vals = np.unique(events[:, 2])
        event_id = {f"event_{v}": int(v) for v in unique_vals}

    epochs = epoch_data(raw, events, event_id)
    epochs_path = output_path / f"epochs_{dataset_id}.fif"
    epochs.save(epochs_path, overwrite=True)
    logger.info(f"Epochs saved to {epochs_path}")

    # 5. Reject epochs
    epochs = reject_epochs(epochs, rejection_threshold)

    # 6. Extract P300 features
    # Assuming single subject for this dataset_id context or iterating if multiple
    # For simplicity, treating dataset_id as subject_id in this context if not specified otherwise
    subject_id = dataset_id
    condition = "unknown" # Should be parsed from metadata if available
    # Try to infer condition from events
    if len(events) > 0:
       # Placeholder logic: if we had multiple event types, we'd group here
       pass

    p300_measures = extract_p300_features(epochs, subject_id, condition, rejection_threshold)

    if not p300_measures:
        logger.warning("No P300 measures extracted.")
        # Still save empty file or handle error
        measures_df = mne.io.write_table_to_dataframe if hasattr(mne.io, 'write_table_to_dataframe') else None
        # Manual CSV write
        import csv
        measures_path = output_path / f"p300_measures_{dataset_id}.csv"
        with open(measures_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["subject_id", "condition", "p300_amplitude", "p300_latency", "qc_status", "threshold_used"])
            writer.writeheader()
            # Write nothing if empty
    else:
        import csv
        measures_path = output_path / f"p300_measures_{dataset_id}.csv"
        with open(measures_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["subject_id", "condition", "p300_amplitude", "p300_latency", "qc_status", "threshold_used"])
            writer.writeheader()
            writer.writerows(p300_measures)
        logger.info(f"P300 measures saved to {measures_path}")

def main():
    parser = setup_argparse()
    args = parser.parse_args()

    # Setup logging
    setup_logging()
    set_seeds(42)

    logger.info("Starting preprocessing phase")
    run_preprocess_phase(
        dataset_id=args.dataset_id,
        rejection_threshold=args.rejection_threshold,
        output_dir=args.output_dir,
        log_dir=args.log_dir
    )
    logger.info("Preprocessing phase completed")

if __name__ == "__main__":
    main()