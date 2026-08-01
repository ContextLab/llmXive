import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
import mne

from config_loader import get_project_root, get_config, ensure_directory
from data_utils import get_subject_ids
from preprocess import get_standard_montage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_epochs(subject_id: str, processed_dir: Path) -> Optional[mne.Epochs]:
    """
    Load preprocessed epochs for a specific subject from data/processed.
    Expects file: data/processed/{subject_id}_epo.fif or data/processed/epo_raw.fif
    depending on how the pipeline was organized. We check standard naming.
    """
    # Try specific subject file first
    file_path = processed_dir / f"{subject_id}_epo.fif"
    if not file_path.exists():
        # Fallback to generic epo_raw.fif if it exists (though typically per-subject)
        file_path = processed_dir / "epo_raw.fif"
    
    if not file_path.exists():
        logger.warning(f"No epoch file found for {subject_id} at {file_path}")
        return None

    try:
        epochs = mne.read_epochs(file_path, preload=True)
        # Ensure events are mapped to conditions if not already in metadata
        # Assuming 'condition' or 'event_id' is in info or metadata
        if epochs.metadata is None:
            # Create basic metadata if missing, assuming event_id maps to condition names
            # This relies on how T018 (epoching) was implemented. 
            # If T018 used event_id 'standard' and 'deviant', we might need to reconstruct.
            # For robustness, we check if 'condition' column exists.
            pass 
        return epochs
    except Exception as e:
        logger.error(f"Failed to load epochs for {subject_id}: {e}")
        return None

def get_subject_epochs_paths(processed_dir: Path) -> List[str]:
    """
    Find all subject epoch files in the processed directory.
    Returns list of subject IDs found.
    """
    # Assuming files are named {sub}_epo.fif
    pattern = processed_dir / "*_epo.fif"
    files = list(pattern.parent.glob(pattern.name))
    # Extract subject IDs
    subject_ids = [f.stem.replace('_epo', '') for f in files]
    return subject_ids

def compute_average_erps(epochs: mne.Epochs, condition: str) -> Optional[mne.Evoked]:
    """
    Compute average ERP for a specific condition ('standard' or 'deviant').
    """
    if epochs.metadata is not None and 'condition' in epochs.metadata.columns:
        mask = epochs.metadata['condition'] == condition
        if not mask.any():
            logger.warning(f"No epochs found for condition '{condition}'")
            return None
        evoked = epochs[mask].average()
    else:
        # Fallback: try to filter by event_id string if metadata is missing
        # This assumes the event_id in the raw data or epochs matches the condition name
        try:
            evoked = epochs[condition].average()
        except KeyError:
            logger.warning(f"Condition '{condition}' not found in epochs. Available: {list(epochs.event_id.keys()) if hasattr(epochs, 'event_id') else 'N/A'}")
            return None
    return evoked

def compute_difference_wave(evoked_deviant: mne.Evoked, evoked_standard: mne.Evoked) -> mne.Evoked:
    """
    Compute difference wave: Deviant - Standard.
    Assumes both evokeds have the same time points and channels.
    """
    if evoked_deviant.times.shape != evoked_standard.times.shape:
        raise ValueError("Time points do not match between deviant and standard evokeds.")
    
    # Create a copy to avoid modifying originals
    diff = evoked_deviant.copy()
    diff.data = evoked_deviant.data - evoked_standard.data
    diff.comment = "Deviant - Standard"
    return diff

def extract_erp_metrics(evoked: mne.Evoked, condition: str, 
                        time_window: Tuple[float, float], 
                        channels: List[str], 
                        baseline: Optional[Tuple[float, float]] = None) -> Dict[str, Any]:
    """
    Extract peak amplitude and latency for a given condition and channel.
    For MMN (US2), we look for the most negative peak in the difference wave.
    
    Args:
        evoked: Evoked object (usually difference wave for MMN)
        condition: Name of the condition (for logging)
        time_window: (start, end) in seconds
        channels: List of channel names to search
        baseline: Optional baseline window tuple
    
    Returns:
        Dictionary with 'amplitude', 'latency', 'peak_detected'
    """
    # Select channels
    try:
        evoked_subset = evoked.copy().pick_channels(channels)
    except Exception:
        # If channels not found, try to pick as many as possible or warn
        logger.warning(f"Channels {channels} not fully found. Attempting partial pick.")
        available = [c for c in channels if c in evoked.ch_names]
        if not available:
            logger.error(f"None of the required channels {channels} found in data.")
            return {'amplitude': np.nan, 'latency': np.nan, 'peak_detected': False}
        evoked_subset = evoked.copy().pick_channels(available)

    # Extract data
    data = evoked_subset.data
    times = evoked_subset.times

    # Find indices for time window
    start_idx = np.where(times >= time_window[0])[0]
    end_idx = np.where(times <= time_window[1])[0]
    
    if len(start_idx) == 0 or len(end_idx) == 0:
        logger.warning(f"Time window {time_window} out of bounds for data.")
        return {'amplitude': np.nan, 'latency': np.nan, 'peak_detected': False}

    start_idx, end_idx = start_idx[0], end_idx[-1]
    
    # Search for most negative peak (MMN is negative deflection)
    # We look across all selected channels and time points in the window
    window_data = data[:, start_idx:end_idx+1]
    window_times = times[start_idx:end_idx+1]
    
    min_val = np.min(window_data)
    min_idx_global = np.argmin(window_data)
    
    # Map flat index back to channel and time
    n_channels = window_data.shape[0]
    channel_idx = min_idx_global // (end_idx - start_idx + 1)
    time_idx = min_idx_global % (end_idx - start_idx + 1)
    
    peak_latency = window_times[time_idx]
    peak_amplitude = min_val
    
    # Check threshold for detection (e.g., > 2.0 uV magnitude for negative peak)
    # SC-005: if no peak >= 2.0 uV in primary window, search secondary.
    # This function handles primary.
    threshold = 2.0 # uV
    peak_detected = abs(peak_amplitude) >= threshold if peak_amplitude < 0 else False
    
    return {
        'amplitude': peak_amplitude,
        'latency': peak_latency,
        'peak_detected': peak_detected
    }

def calculate_snr(evoked: mne.Evoked, signal_window: Tuple[float, float], 
                  noise_window: Tuple[float, float]) -> float:
    """
    Calculate Signal-to-Noise Ratio.
    Signal: RMS of the average in the signal window.
    Noise: RMS of the pre-stimulus baseline (or specified noise window).
    """
    times = evoked.times
    data = evoked.data # Shape: (n_channels, n_times)

    # Signal window
    sig_start = np.where(times >= signal_window[0])[0][0]
    sig_end = np.where(times <= signal_window[1])[0][-1]
    sig_data = data[:, sig_start:sig_end+1]
    signal_rms = np.sqrt(np.mean(sig_data**2))

    # Noise window (usually pre-stimulus)
    if noise_window[0] < times[0] or noise_window[1] > times[-1]:
        # Fallback to full pre-stimulus if specified window is out of bounds
        noise_start = 0
        noise_end = np.where(times < 0)[0][-1] if np.any(times < 0) else 0
    else:
        noise_start = np.where(times >= noise_window[0])[0][0]
        noise_end = np.where(times <= noise_window[1])[0][-1]
    
    if noise_end <= noise_start:
        logger.warning("Noise window invalid, cannot calculate SNR.")
        return 0.0

    noise_data = data[:, noise_start:noise_end+1]
    noise_rms = np.sqrt(np.mean(noise_data**2))

    if noise_rms == 0:
        return np.inf
    return signal_rms / noise_rms

def save_intermediate_erps(evoked_standard: mne.Evoked, evoked_deviant: mne.Evoked, 
                           diff_wave: mne.Evoked, subject_id: str, output_dir: Path):
    """
    Save intermediate ERP files for debugging/inspection.
    """
    ensure_directory(output_dir)
    # Naming convention: sub-XX_standard_evoked.fif, etc.
    evoked_standard.save(output_dir / f"{subject_id}_standard_evoked.fif", overwrite=True)
    evoked_deviant.save(output_dir / f"{subject_id}_deviant_evoked.fif", overwrite=True)
    diff_wave.save(output_dir / f"{subject_id}_diff_evoked.fif", overwrite=True)

def run_extraction_pipeline():
    """
    Main pipeline to extract MMN metrics for all subjects.
    Produces results/metrics.csv with required columns.
    """
    root = get_project_root()
    config = get_config()
    processed_dir = root / "data" / "processed"
    results_dir = root / "results"
    ensure_directory(results_dir)

    # Configuration for MMN extraction
    # Primary window: 150-250ms
    primary_window = (0.150, 0.250)
    # Secondary window fallback: 100-300ms
    secondary_window = (0.100, 0.300)
    # Channels of interest
    target_channels = ['Fz', 'FCz']
    # Baseline for SNR (pre-stimulus)
    noise_window = (-0.200, 0.0)
    # Signal window for SNR (around peak)
    signal_window = (0.150, 0.250)

    subjects = get_subject_ids() # Or use get_subject_epochs_paths(processed_dir)
    # If get_subject_ids returns raw IDs, we need to ensure they match epoch files
    # Let's use the files found in processed dir to be safe
    subject_files = get_subject_epochs_paths(processed_dir)
    if not subject_files:
        logger.error("No subject epoch files found in data/processed. Pipeline cannot run.")
        return

    metrics_data = []

    for sub_id in subject_files:
        logger.info(f"Processing subject: {sub_id}")
        
        epochs = load_epochs(sub_id, processed_dir)
        if epochs is None:
            logger.warning(f"Skipping {sub_id} due to missing epochs.")
            continue

        # Compute Average ERPs
        evoked_std = compute_average_erps(epochs, 'standard')
        evoked_dev = compute_average_erps(epochs, 'deviant')

        if evoked_std is None or evoked_dev is None:
            logger.warning(f"Skipping {sub_id} due to missing conditions.")
            continue

        # Compute Difference Wave
        try:
            diff_wave = compute_difference_wave(evoked_dev, evoked_std)
        except Exception as e:
            logger.error(f"Failed to compute difference wave for {sub_id}: {e}")
            continue

        # Save intermediate files
        save_intermediate_erps(evoked_std, evoked_dev, diff_wave, sub_id, processed_dir)

        # Extract Metrics for Standard (for completeness, though MMN is diff)
        # Note: T027 asks for standard_amplitude/latency too. We extract from standard ERP.
        # We look for the most negative peak in the same window for standard? 
        # Usually standard doesn't have MMN, but we extract the metric as requested.
        
        std_metrics = extract_erp_metrics(evoked_std, 'standard', primary_window, target_channels)
        dev_metrics = extract_erp_metrics(evoked_dev, 'deviant', primary_window, target_channels)
        diff_metrics = extract_erp_metrics(diff_wave, 'diff', primary_window, target_channels)

        # Fallback logic for MMN (Difference Wave) if peak not detected in primary
        final_diff_metrics = diff_metrics
        if not diff_metrics['peak_detected']:
            logger.info(f"Primary peak not detected for {sub_id}, checking secondary window.")
            sec_metrics = extract_erp_metrics(diff_wave, 'diff', secondary_window, target_channels)
            if sec_metrics['peak_detected']:
                final_diff_metrics = sec_metrics
                logger.info(f"Secondary peak detected for {sub_id} at {sec_metrics['latency']}s")
            else:
                logger.info(f"No peak detected for {sub_id} in either window.")

        # Calculate SNR on the difference wave
        try:
            snr = calculate_snr(diff_wave, signal_window, noise_window)
        except Exception as e:
            logger.warning(f"SNR calculation failed for {sub_id}: {e}")
            snr = np.nan

        # Construct row
        row = {
            'participant_id': sub_id,
            'standard_amplitude': std_metrics['amplitude'],
            'standard_latency': std_metrics['latency'],
            'deviant_amplitude': dev_metrics['amplitude'],
            'deviant_latency': dev_metrics['latency'],
            'peak_detected': final_diff_metrics['peak_detected'],
            'snr': snr
        }
        metrics_data.append(row)

    # Create DataFrame
    df = pd.DataFrame(metrics_data)
    
    # Ensure correct types
    df['peak_detected'] = df['peak_detected'].astype(bool)
    
    # Save to CSV
    output_path = results_dir / "metrics.csv"
    df.to_csv(output_path, index=False)
    logger.info(f"Metrics saved to {output_path}")
    logger.info(f"Total participants processed: {len(df)}")
    logger.info(f"Participants with peak detected: {df['peak_detected'].sum()}")

    return df

def main():
    run_extraction_pipeline()

if __name__ == "__main__":
    main()
