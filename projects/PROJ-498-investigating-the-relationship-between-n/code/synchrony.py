import os
import sys
import csv
import json
import logging
from typing import Dict, List, Tuple, Set, Optional
import numpy as np
import mne
from pathlib import Path

# Import local config and logging
try:
    from config import ensure_directories
    from logging_setup import get_logger
    from update_state_hashes import compute_file_hash, save_state
except ImportError:
    # Fallback for standalone execution if needed, though project structure implies these exist
    ensure_directories = lambda: None
    def get_logger(name):
        return logging.getLogger(name)

# --- Electrode Mapping Logic ---

def get_region_for_electrode(electrode: str) -> Optional[str]:
    """Maps an electrode name to a brain region."""
    electrode = electrode.upper()
    dlpxc = {'F3', 'F4', 'FC3', 'FC4'}
    parietal = {'P3', 'P4', 'CP3', 'CP4'}
    
    if electrode in dlpxc:
        return 'DLPFC'
    elif electrode in parietal:
        return 'Parietal'
    return None

def get_all_electrode_pairs(electrodes: List[str]) -> List[Tuple[str, str]]:
    """Generates all unique pairs from a list of electrodes."""
    pairs = []
    for i in range(len(electrodes)):
        for j in range(i + 1, len(electrodes)):
            pairs.append((electrodes[i], electrodes[j]))
    return pairs

def get_cross_region_pairs(region1: str, region2: str, electrodes: List[str]) -> List[Tuple[str, str]]:
    """Gets pairs where one electrode is in region1 and the other in region2."""
    r1_electrodes = [e for e in electrodes if get_region_for_electrode(e) == region1]
    r2_electrodes = [e for e in electrodes if get_region_for_electrode(e) == region2]
    
    pairs = []
    for e1 in r1_electrodes:
        for e2 in r2_electrodes:
            pairs.append((e1, e2))
    return pairs

def validate_electrode_presence(electrodes: List[str], required: List[str]) -> bool:
    """Checks if all required electrodes are present in the montage."""
    present = set(e.upper() for e in electrodes)
    return all(r.upper() in present for r in required)

def get_pair_id(pair: Tuple[str, str]) -> str:
    """Generates a unique ID for an electrode pair."""
    e1, e2 = sorted([pair[0].upper(), pair[1].upper()])
    return f"{e1}-{e2}"

def is_valid_pair(pair: Tuple[str, str]) -> bool:
    """Checks if a pair represents a valid DLPFC-Parietal connection."""
    r1 = get_region_for_electrode(pair[0])
    r2 = get_region_for_electrode(pair[1])
    return (r1 == 'DLPFC' and r2 == 'Parietal') or (r1 == 'Parietal' and r2 == 'DLPFC')

def get_region_pairs() -> List[Tuple[str, str]]:
    """Returns the list of region pairs to analyze."""
    return [('DLPFC', 'Parietal')]

def get_pair_region_type(pair: Tuple[str, str]) -> str:
    """Returns 'cross-region' or 'intra-region'."""
    r1 = get_region_for_electrode(pair[0])
    r2 = get_region_for_electrode(pair[1])
    if r1 and r2 and r1 != r2:
        return 'cross-region'
    return 'intra-region'

# --- Filtering Logic ---

def filter_bandpower(data: np.ndarray, sfreq: float, low: float, high: float) -> np.ndarray:
    """Applies a bandpass filter to the data."""
    # Using MNE for robust filtering
    info = mne.create_info(ch_names=['ch'], sfreq=sfreq, ch_types='eeg')
    raw = mne.io.RawArray(data.reshape(1, -1), info)
    raw.filter(low, high, fir_design='firwin', verbose=False)
    return raw.get_data()[0]

def get_theta_filtered_data(data: np.ndarray, sfreq: float) -> np.ndarray:
    """Filters data for theta band (4-7 Hz)."""
    return filter_bandpower(data, sfreq, 4, 7)

def get_gamma_filtered_data(data: np.ndarray, sfreq: float) -> np.ndarray:
    """Filters data for gamma band (30-45 Hz)."""
    return filter_bandpower(data, sfreq, 30, 45)

# --- Synchrony Calculation ---

def prepare_data_for_synchrony(epochs: mne.Epochs, tmin: float, tmax: float) -> Tuple[np.ndarray, float]:
    """
    Extracts pre-stimulus data from epochs.
    Returns: (data array of shape [n_epochs, n_channels, n_times], sfreq)
    """
    # Select time window
    data = epochs.copy().crop(tmin=tmin, tmax=tmax).get_data()
    sfreq = epochs.info['sfreq']
    return data, sfreq

def compute_wpli(data1: np.ndarray, data2: np.ndarray) -> float:
    """
    Computes the weighted Phase Lag Index (wPLI).
    data1, data2: arrays of shape [n_epochs, n_times]
    """
    if data1.shape != data2.shape:
        raise ValueError("Data shapes must match")
    
    n_epochs, n_times = data1.shape
    wpli_sum = 0.0
    count = 0

    for ep in range(n_epochs):
        # Hilbert transform to get instantaneous phase
        # Using scipy for Hilbert to avoid MNE overhead for simple extraction if needed, 
        # but MNE's hilbert is robust. Let's use numpy/scipy directly for speed.
        try:
            from scipy.signal import hilbert
        except ImportError:
            raise ImportError("scipy is required for wPLI calculation")

        h1 = hilbert(data1[ep])
        h2 = hilbert(data2[ep])
        
        phase_diff = np.angle(h1) - np.angle(h2)
        cos_phase_diff = np.cos(phase_diff)
        sin_phase_diff = np.sin(phase_diff)
        
        # wPLI formula: |E[Im(X)]| / E[|Im(X)|]
        # Im(X) = sin(phase_diff)
        im_x = sin_phase_diff
        
        numerator = np.abs(np.mean(im_x))
        denominator = np.mean(np.abs(im_x))
        
        if denominator > 1e-9:
            wpli_sum += numerator / denominator
            count += 1
        
    return wpli_sum / count if count > 0 else 0.0

def compute_plv(data1: np.ndarray, data2: np.ndarray) -> float:
    """
    Computes the Phase Locking Value (PLV).
    """
    if data1.shape != data2.shape:
        raise ValueError("Data shapes must match")
    
    n_epochs, n_times = data1.shape
    plv_sum = 0.0
    count = 0

    for ep in range(n_epochs):
        try:
            from scipy.signal import hilbert
        except ImportError:
            raise ImportError("scipy is required for PLV calculation")

        h1 = hilbert(data1[ep])
        h2 = hilbert(data2[ep])
        
        phase_diff = np.angle(h1) - np.angle(h2)
        
        # PLV = |E[exp(i * phase_diff)]|
        plv_val = np.abs(np.mean(np.exp(1j * phase_diff)))
        plv_sum += plv_val
        count += 1
        
    return plv_sum / count if count > 0 else 0.0

def compute_synchrony_metrics(epochs: mne.Epochs, bands: Dict[str, Tuple[float, float]], tmin: float, tmax: float) -> Dict:
    """
    Computes synchrony metrics for all DLPFC-Parietal pairs and bands.
    Returns a dict: { (pair_id, band_name): value }
    """
    # Prepare data
    data, sfreq = prepare_data_for_synchrony(epochs, tmin, tmax)
    n_channels = data.shape[1]
    ch_names = [ch.upper() for ch in epochs.ch_names]
    
    # Identify channel indices for DLPFC and Parietal
    dlpxc_indices = [i for i, ch in enumerate(ch_names) if get_region_for_electrode(ch) == 'DLPFC']
    parietal_indices = [i for i, ch in enumerate(ch_names) if get_region_for_electrode(ch) == 'Parietal']
    
    metrics = {}
    
    # Define pairs
    pairs = []
    for i in dlpxc_indices:
        for j in parietal_indices:
            pairs.append((ch_names[i], ch_names[j]))
    
    for ch1, ch2 in pairs:
        pair_id = get_pair_id((ch1, ch2))
        idx1 = ch_names.index(ch1)
        idx2 = ch_names.index(ch2)
        
        # Extract data for this pair across epochs
        d1 = data[:, idx1, :]
        d2 = data[:, idx2, :]
        
        for band_name, (low, high) in bands.items():
            # Filter
            d1_filt = np.apply_along_axis(lambda x: filter_bandpower(x, sfreq, low, high), 1, d1)
            d2_filt = np.apply_along_axis(lambda x: filter_bandpower(x, sfreq, low, high), 1, d2)
            
            # Compute wPLI (or PLV)
            # Using wPLI as primary metric as per spec preference
            wpli_val = compute_wpli(d1_filt, d2_filt)
            
            key = (pair_id, band_name)
            metrics[key] = wpli_val
            
    return metrics

def save_synchrony_metrics(metrics: Dict, subject_id: str, output_path: str):
    """
    Saves synchrony metrics to a CSV file.
    Format: subject_id, pair_id, band, value
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    rows = []
    for (pair_id, band), value in metrics.items():
        rows.append({
            'subject_id': subject_id,
            'pair_id': pair_id,
            'band': band,
            'value': value
        })
    
    if rows:
        df = pd.DataFrame(rows)
        # Sort for consistency
        df = df.sort_values(by=['subject_id', 'pair_id', 'band'])
        df.to_csv(output_path, index=False)
    else:
        # Write empty file with headers if no data
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['subject_id', 'pair_id', 'band', 'value'])

def main():
    """
    Main entry point for saving synchrony metrics.
    Assumes epochs have been processed and saved by T019.
    """
    logger = get_logger('synchrony')
    logger.info("Starting synchrony metrics computation and saving.")
    
    # Configuration
    # Assuming pre-stimulus window is -1000ms to 0ms based on T016 (epoch -1000 to +2000)
    # Spec T024 says "pre-stimulus window (a sufficiently long baseline period prior to stimulus onset)"
    # We use -1000 to 0 as the baseline.
    tmin = -1.0
    tmax = 0.0
    
    bands = {
        'theta': (4, 7),
        'gamma': (30, 45)
    }
    
    data_dir = Path('data/processed')
    metrics_dir = Path('data/metrics')
    ensure_directories() # Ensures data/metrics exists if config handles it, else we mkdir
    
    if not data_dir.exists():
        logger.error(f"Data directory {data_dir} not found. Run T019 first.")
        sys.exit(1)
    
    # Find subject files (assuming .fif or similar from T019)
    # T019 saves clean epochs. We assume a standard naming convention like sub-{id}_epochs.fif
    subject_files = list(data_dir.glob('sub-*_epochs.fif'))
    
    if not subject_files:
        logger.warning("No subject epoch files found in data/processed. Exiting.")
        sys.exit(0)
    
    # Aggregate all metrics into a single CSV as per T025 requirement
    # "Save synchrony matrices to data/metrics/synchrony_metrics.csv"
    all_rows = []
    
    for fpath in subject_files:
        subject_id = fpath.stem.replace('_epochs', '')
        logger.info(f"Processing {subject_id}...")
        
        try:
            epochs = mne.read_epochs(fpath, verbose=False)
            metrics = compute_synchrony_metrics(epochs, bands, tmin, tmax)
            
            # Convert to list of dicts for aggregation
            for (pair_id, band), value in metrics.items():
                all_rows.append({
                    'subject_id': subject_id,
                    'pair_id': pair_id,
                    'band': band,
                    'value': value
                })
        except Exception as e:
            logger.error(f"Failed to process {subject_id}: {e}")
            continue
    
    # Save aggregated CSV
    output_csv = metrics_dir / 'synchrony_metrics.csv'
    if all_rows:
        df = pd.DataFrame(all_rows)
        df = df.sort_values(by=['subject_id', 'pair_id', 'band'])
        df.to_csv(output_csv, index=False)
        logger.info(f"Saved synchrony metrics to {output_csv}")
    else:
        # Create empty file with headers
        with open(output_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['subject_id', 'pair_id', 'band', 'value'])
        logger.warning("No metrics computed. Created empty CSV with headers.")
    
    # Hash the output file as required by T004 dependency
    if output_csv.exists():
        hash_val = compute_file_hash(str(output_csv))
        logger.info(f"Hash for {output_csv}: {hash_val}")
        # Update state if needed, but T004 handles the global state update usually.
        # We just ensure the file exists and is valid.

if __name__ == '__main__':
    main()
