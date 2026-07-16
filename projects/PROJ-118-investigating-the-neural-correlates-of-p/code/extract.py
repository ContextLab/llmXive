import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
import mne

# Import existing utilities from sibling modules if needed
# from data_utils import load_config_and_validate
# from analyze_rejection import identify_excluded_participants

logger = logging.getLogger(__name__)

# Constants derived from project context
PRIMARY_WINDOW = (0.150, 0.250)  # 150-250 ms
SECONDARY_WINDOW = (0.100, 0.300)  # 100-300 ms
PEAK_THRESHOLD_UMV = 2.0  # Microvolts
TARGET_CHANNELS = ['Fz', 'FCz']

def load_epochs(epochs_path: Path) -> mne.Epochs:
    """Load epochs from a .fif file."""
    if not epochs_path.exists():
        raise FileNotFoundError(f"Epochs file not found: {epochs_path}")
    logger.info(f"Loading epochs from {epochs_path}")
    epochs = mne.read_epochs(epochs_path, preload=True)
    return epochs

def get_subject_epochs_paths(epochs_dir: Path) -> Dict[str, Path]:
    """Get paths to epochs files for all subjects."""
    paths = {}
    if not epochs_dir.exists():
        raise FileNotFoundError(f"Epochs directory not found: {epochs_dir}")
    
    for subject_dir in sorted(epochs_dir.iterdir()):
        if subject_dir.is_dir() and subject_dir.name.startswith('sub-'):
            epochs_file = subject_dir / 'epo_raw.fif'
            if epochs_file.exists():
                paths[subject_dir.name] = epochs_file
    return paths

def compute_average_erps(epochs: mne.Epochs, condition: str) -> mne.Evoked:
    """Compute average ERP for a specific condition."""
    if condition not in epochs.event_id:
        logger.warning(f"Condition {condition} not found in epochs. Available: {list(epochs.event_id.keys())}")
        # Fallback: try to find similar condition name
        matching = [k for k in epochs.event_id.keys() if condition.lower() in k.lower()]
        if matching:
            condition = matching[0]
            logger.info(f"Using matched condition: {condition}")
        else:
            raise ValueError(f"Condition {condition} not found in epochs")
    
    erp = epochs[condition].average()
    return erp

def compute_difference_wave(standard_erp: mne.Evoked, deviant_erp: mne.Evoked) -> mne.Evoked:
    """Compute difference wave (Deviant - Standard)."""
    # Ensure channels match
    common_chs = list(set(standard_erp.ch_names) & set(deviant_erp.ch_names))
    if not common_chs:
        raise ValueError("No common channels between standard and deviant ERPs")
    
    # Reorder and select common channels
    std = standard_erp.copy().pick_channels(common_chs)
    dev = deviant_erp.copy().pick_channels(common_chs)
    
    diff = dev - std
    diff.comment = 'Diff (Deviant - Standard)'
    return diff

def save_difference_waves(diff_erp: mne.Evoked, output_path: Path):
    """Save difference wave to file."""
    diff_erp.save(output_path, overwrite=True)
    logger.info(f"Saved difference wave to {output_path}")

def extract_erp_metrics(erp: mne.Evoked, window: Tuple[float, float], 
                        channels: List[str] = TARGET_CHANNELS) -> Tuple[Optional[float], Optional[float]]:
    """
    Extract peak amplitude and latency in a given time window.
    Returns (amplitude_µV, latency_s) or (None, None) if no peak found.
    """
    # Select channels
    try:
        erp_picked = erp.copy().pick_channels(channels)
    except Exception:
        # If specific channels not found, try closest or all
        erp_picked = erp.copy()
    
    # Get time and data
    times = erp_picked.times
    data = erp_picked.data  # shape: (n_channels, n_times)
    
    # Find indices for the window
    t_min, t_max = window
    idx_start = np.searchsorted(times, t_min)
    idx_end = np.searchsorted(times, t_max)
    
    if idx_start >= idx_end or idx_end > len(times):
        logger.warning(f"Window {window} out of bounds for data times {times[0]} to {times[-1]}")
        return None, None
    
    # Find minimum (most negative) value in the window across selected channels
    window_data = data[:, idx_start:idx_end]
    min_idx_global = np.argmin(window_data)
    
    # Convert flat index to (channel_idx, time_idx)
    chan_idx = min_idx_global // window_data.shape[1]
    time_idx = min_idx_global % window_data.shape[1]
    
    abs_time_idx = idx_start + time_idx
    latency = times[abs_time_idx]
    amplitude = window_data[chan_idx, time_idx]
    
    return amplitude, latency

def calculate_snr(erp: mne.Evoked, baseline_window: Tuple[float, float] = (-0.2, 0.0)) -> float:
    """
    Calculate Signal-to-Noise Ratio.
    Signal: peak amplitude (absolute value)
    Noise: standard deviation of baseline period
    """
    times = erp.times
    data = erp.data
    
    # Baseline indices
    t_min, t_max = baseline_window
    idx_start = np.searchsorted(times, t_min)
    idx_end = np.searchsorted(times, t_max)
    
    if idx_start >= idx_end:
        return 0.0
    
    baseline_data = data[:, idx_start:idx_end]
    noise = np.std(baseline_data)
    
    if noise == 0:
        return 0.0
    
    # Use maximum absolute amplitude as signal
    peak_amp = np.max(np.abs(data))
    snr = peak_amp / noise
    return snr

def save_intermediate_erps(standard_erp: mne.Evoked, deviant_erp: mne.Evoked, 
                           diff_erp: mne.Evoked, subject_id: str, output_dir: Path):
    """Save intermediate ERP objects for inspection."""
    output_dir.mkdir(parents=True, exist_ok=True)
    standard_erp.save(output_dir / f'{subject_id}_std-ave.fif', overwrite=True)
    deviant_erp.save(output_dir / f'{subject_id}_dev-ave.fif', overwrite=True)
    diff_erp.save(output_dir / f'{subject_id}_diff-ave.fif', overwrite=True)

def run_extraction_pipeline(epochs_dir: Path, output_path: Path, 
                            excluded_subjects: Optional[List[str]] = None):
    """
    Run the full metric extraction pipeline.
    Produces results/metrics.csv with columns:
    participant_id, standard_amplitude, standard_latency, deviant_amplitude, 
    deviant_latency, peak_detected, snr
    """
    if excluded_subjects is None:
        excluded_subjects = []
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    subject_paths = get_subject_epochs_paths(epochs_dir)
    metrics_list = []
    
    for subject_id, epochs_file in subject_paths.items():
        if subject_id in excluded_subjects:
            logger.info(f"Skipping excluded subject: {subject_id}")
            continue
        
        logger.info(f"Processing {subject_id}")
        try:
            # Load epochs
            epochs = load_epochs(epochs_file)
            
            # Compute average ERPs
            std_erp = compute_average_erps(epochs, 'standard')
            dev_erp = compute_average_erps(epochs, 'deviant')
            
            # Compute difference wave
            diff_erp = compute_difference_wave(std_erp, dev_erp)
            
            # Save intermediate results (optional but useful)
            save_intermediate_erps(std_erp, dev_erp, diff_erp, subject_id, 
                                   output_path.parent / 'intermediate')
            
            # Extract metrics from Standard ERP
            std_amp, std_lat = extract_erp_metrics(std_erp, PRIMARY_WINDOW)
            if std_amp is None:
                std_amp, std_lat = extract_erp_metrics(std_erp, SECONDARY_WINDOW)
            
            # Extract metrics from Deviant ERP
            dev_amp, dev_lat = extract_erp_metrics(dev_erp, PRIMARY_WINDOW)
            if dev_amp is None:
                dev_amp, dev_lat = extract_erp_metrics(dev_erp, SECONDARY_WINDOW)
            
            # Extract peak from Difference Wave
            diff_amp, diff_lat = extract_erp_metrics(diff_erp, PRIMARY_WINDOW)
            peak_detected = True
            
            # Fallback logic per SC-005
            if diff_amp is None or abs(diff_amp) < PEAK_THRESHOLD_UMV:
                diff_amp, diff_lat = extract_erp_metrics(diff_erp, SECONDARY_WINDOW)
                if diff_amp is None or abs(diff_amp) < PEAK_THRESHOLD_UMV:
                    peak_detected = False
                    # Still record the best found value or None
                    if diff_amp is None:
                        diff_amp = 0.0
                        diff_lat = 0.0
            
            # Calculate SNR on the difference wave
            snr = calculate_snr(diff_erp)
            
            metrics_list.append({
                'participant_id': subject_id,
                'standard_amplitude': std_amp if std_amp is not None else np.nan,
                'standard_latency': std_lat if std_lat is not None else np.nan,
                'deviant_amplitude': dev_amp if dev_amp is not None else np.nan,
                'deviant_latency': dev_lat if dev_lat is not None else np.nan,
                'peak_detected': peak_detected,
                'snr': snr
            })
            
        except Exception as e:
            logger.error(f"Failed to process {subject_id}: {e}", exc_info=True)
            # Retain participant with flagged status for prevalence analysis
            metrics_list.append({
                'participant_id': subject_id,
                'standard_amplitude': np.nan,
                'standard_latency': np.nan,
                'deviant_amplitude': np.nan,
                'deviant_latency': np.nan,
                'peak_detected': False,
                'snr': np.nan
            })
    
    # Create DataFrame
    df = pd.DataFrame(metrics_list)
    
    # Ensure correct types
    df['peak_detected'] = df['peak_detected'].astype(bool)
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Saved metrics to {output_path}")
    logger.info(f"Total participants processed: {len(df)}")
    logger.info(f"Participants with peak detected: {df['peak_detected'].sum()}")
    logger.info(f"Participants without peak (flagged for exclusion from t-test): {(~df['peak_detected']).sum()}")
    
    return df

def main():
    """Entry point for the extraction pipeline."""
    # Default paths based on project structure
    base_dir = Path(__file__).parent.parent
    epochs_dir = base_dir / 'data' / 'processed'
    output_file = base_dir / 'results' / 'metrics.csv'
    
    # Load excluded participants if available
    excluded_file = base_dir / 'data' / 'processed' / 'rejected_participants.log'
    excluded_subjects = []
    if excluded_file.exists():
        with open(excluded_file, 'r') as f:
            excluded_subjects = [line.strip() for line in f if line.strip()]
    
    run_extraction_pipeline(epochs_dir, output_file, excluded_subjects)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()